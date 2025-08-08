import os
import sys
import asyncio

from dotenv import load_dotenv
from loguru import logger

from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor, RTVIServerMessageFrame
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService, LiveOptions
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
from pipecat.transcriptions.language import Language
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from personas.confused_customer import persona as confused_customer_persona
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.frames.frames import TransportMessageUrgentFrame, LLMFullResponseEndFrame, LLMTextFrame, Frame, \
    LLMFullResponseStartFrame
from pipecat.processors.aggregators.llm_response import LLMFullResponseAggregator

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json
from personas.budget_customer import persona as cost_sensitive_persona
from personas.frustrated_customer import persona as angry_customer_persona
from personas.struggling_customer import persona as struggling_customer_persona
from personas.concerned_customer import persona as concerned_customer_persona

load_dotenv(override=True)


def get_sentiment(transcript: str):
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18",
                       temperature=0.8,
                       max_tokens=None,
                       timeout=None,
                       max_retries=2)

    # Building the compliance checker prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         """Given the following conversation (which may be partial and ongoing), analyze the overall sentiment expressed so far.
            Assign a single sentiment score on a scale of 1 to 100, where 1 indicates extremely negative sentiment, 50 is neutral, and 100 is extremely positive.
            Only return the score as a single integer (no explanations or extra text).
        """),
        ("user", "{input}")
    ])

    chain = prompt | model
    response = chain.invoke({"input": transcript})

    try:
        score = response.content
        logger.debug(f"sentiment score: {score}")
        if isinstance(score, str):
            return int(score)
        else:
            return 70
    except Exception:
        return 70


class SentimentAnalysisProcessor(FrameProcessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._accumulated_text = ""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # Start accumulating when LLM response begins
        if isinstance(frame, LLMFullResponseStartFrame):
            self._accumulated_text = ""

        # Accumulate text chunks
        elif isinstance(frame, LLMTextFrame):
            self._accumulated_text += frame.text

        # Process sentiment when response is complete
        elif isinstance(frame, LLMFullResponseEndFrame):
            if self._accumulated_text:
                # Run sentiment analysis asynchronously without blocking
                self.create_task(self._analyze_and_send_sentiment(self._accumulated_text))
                self._accumulated_text = ""

        # Always forward the frame immediately
        await self.push_frame(frame, direction)

    async def _analyze_and_send_sentiment(self, text: str):
        """Analyze sentiment asynchronously and send result"""
        try:
            sentiment = await self._analyze_sentiment(text)
            await self.push_frame(
                RTVIServerMessageFrame(
                    data={
                        "type": "sentiment-analysis",
                        "sentiment": sentiment,
                        "text": text,
                    }
                )
            )
        except Exception as e:
            print(f"Sentiment analysis error: {e}")

    async def _analyze_sentiment(self, text: str) -> int:
        # Run in thread pool to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_sentiment, text)


async def run_bot(webrtc_connection, persona_name: str = "cost_sensitive"):
    pipecat_transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    confidence=0.8,  # Higher = more strict (default: 0.7)
                    start_secs=0.3,  # Longer before detecting speech (default: 0.2)
                    stop_secs=1.2,  # Longer silence before stopping (default: 0.8)
                    min_volume=0.7  # Higher volume threshold (default: 0.6)
                )
            ),
            audio_out_10ms_chunks=1,
        ),
    )

    llm = OpenAILLMService(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        params=OpenAILLMService.InputParams(
            temperature=0.7,
        )
    )

    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
        live_options=LiveOptions(
            model="nova-3-general",
            language=Language.EN,
            smart_format=True
        )
    )

    # Map the incoming persona name to the actual prompt string. Default to
    # the cost-sensitive customer if the name is unrecognised.
    _persona_map = {
        "cost_sensitive": cost_sensitive_persona,
        "confused_customer": confused_customer_persona,
        "frustrated_customer": angry_customer_persona,
        "concerned_customer": concerned_customer_persona,
        "struggling_customer": struggling_customer_persona,
    }

    persona_prompt = _persona_map.get(persona_name, cost_sensitive_persona)

    # Map the persona name to the voice id
    _voice_map = {
        "cost_sensitive": "4NejU5DwQjevnR6mh3mb",
        "confused_customer": "EIsgvJT3rwoPvRFG6c4n",
        "frustrated_customer": "x3gYeuNB0kLLYxOZsaSh",
        "concerned_customer": "x3gYeuNB0kLLYxOZsaSh",
        "struggling_customer": "EIsgvJT3rwoPvRFG6c4n",
    }

    voice_id = _voice_map.get(persona_name, "aura-luna-en")

    context = OpenAILLMContext(
        [
            {
                "role": "system",
                "content": persona_prompt,
            }
        ],
    )
    context_aggregator = llm.create_context_aggregator(context)

    # tts = DeepgramTTSService(
    #     api_key=os.getenv("DEEPGRAM_API_KEY"),
    #     voice="aura-luna-en",
    #     sample_rate=24000,
    #     encoding="linear16"
    # )

    ## Use this for demo. Its better quality
    tts = ElevenLabsTTSService(  # ElevenLabs TTS
    api_key=os.getenv("ELEVENLABS_API_KEY"),
    voice_id=voice_id,
    model="eleven_flash_v2_5",
    sample_rate=24000
    )

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # Sentiment aggregator plugged after the LLM
    sentiment_agg = SentimentAnalysisProcessor()

    pipeline = Pipeline(
        [
            pipecat_transport.input(),
            stt,
            context_aggregator.user(),
            rtvi,
            llm,  # LLM
            sentiment_agg,
            tts,
            pipecat_transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
            allow_interruptions=False,
        ),
        observers=[RTVIObserver(rtvi)],

    )

    # Handle client connection
    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        # Signal bot is ready to receive messages
        await rtvi.set_bot_ready()
        # Removed the initial user frame – the customer persona should wait for the agent to initiate the conversation.

    @pipecat_transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Pipecat Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)
