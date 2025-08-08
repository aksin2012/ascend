#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import argparse
import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Dict

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

from fastapi.middleware.cors import CORSMiddleware

import uvicorn
from bot import run_bot
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger

from pipecat.transports.network.webrtc_connection import IceServer, SmallWebRTCConnection

# Load environment variables
load_dotenv(override=True)

app = FastAPI()

# Store connections by pc_id
pcs_map: Dict[str, SmallWebRTCConnection] = {}

ice_servers = [
    IceServer(
        urls="stun:stun.l.google.com:19302",
    )
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend: ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/src", StaticFiles(directory="src"), name="static")


@app.get("/api/personas")
async def get_personas():
    personas = [
        {
            "id": "frustrated_customer",
            "title": "The Frustrated Customer",
            "desc": "Angry, direct, and demands clear, fee-free pricing.",
            "img": "./public/frustrated_customer.png",
            "address": "4121 Oak Creek Dr, Austin, TX 78727",
            "birthDate": "07/12/1994",
            "email": "john.dean@gmail.com",
            "ownership": "Owner",
            "language": "English"
        },
        {
            "id": "confused_customer",
            "title": "The Confused Customer",
            "desc": "Polite but overwhelmed and needs simple, step-by-step help.",
            "img": "./public/confused_customer.png",
            "address": "2 Cedar Court, Dallas, TX 75238",
            "birthDate": "08/12/1994",
            "email": "sarah.hill@email.com",
            "ownership": "Renter",
            "language": "English"
        },
        {
            "id": "budget_customer",
            "title": "The Budget Customer",
            "desc": "Focused on finding the lowest price and avoiding hidden fees.",
            "img": "./public/budget_customer.png",
            "address": "10500 Cloisters Dr, Fort Worth, TX 3941",
            "birthDate": "08/12/1994",
            "email": "taylor.braxton@gmail.com",
            "ownership": "Renter",
            "language": "English"
        },
        {
            "id": "struggling_customer",
            "title": "The Struggling Customer",
            "desc": "Facing hardship and seeks a fair, respectful payment plan.",
            "img": "./public/struggling_customer.png",
            "address": "1835 Maplewood Dr, Houston, TX 77009",
            "birthDate": "08/12/1994",
            "email": "jordan.rivera@email.com",
            "ownership": "Renter",
            "language": "English"
        },
        {
            "id": "concerned_customer",
            "title": "The Concerned Customer",
            "desc": "Surprised by a high bill and wants answers without excuses.",
            "img": "./public/concerned_customer.png",
            "address": "1835 Maplewood Dr, Houston, TX 77009",
            "birthDate": "08/12/1994",
            "email": "jordan.rivera@email.com",
            "ownership": "Renter",
            "language": "English"
        },
        {
            "id": "create_customer",
            "title": "Create Your Own",
            "desc": "Write your own customer scenario and behavior summary.",
            "img": "./public/create_customer.png",
        }
    ]

    return JSONResponse(content=personas)


@app.post("/api/offer")
async def offer(persona: str, request: dict, background_tasks: BackgroundTasks):
    pc_id = request.get("pc_id")
    logger.info(f"Using persona: {persona}")

    if pc_id and pc_id in pcs_map:
        pipecat_connection = pcs_map[pc_id]
        logger.info(f"Reusing existing connection for pc_id: {pc_id}")
        await pipecat_connection.renegotiate(sdp=request["sdp"], type=request["type"])
    else:
        pipecat_connection = SmallWebRTCConnection(ice_servers)
        await pipecat_connection.initialize(sdp=request["sdp"], type=request["type"])

        @pipecat_connection.event_handler("closed")
        async def handle_disconnected(webrtc_connection: SmallWebRTCConnection):
            logger.info(f"Discarding peer connection for pc_id: {webrtc_connection.pc_id}")
            pcs_map.pop(webrtc_connection.pc_id, None)

        # Forward the persona name so that the bot behaves accordingly
        background_tasks.add_task(run_bot, pipecat_connection, persona)

    answer = pipecat_connection.get_answer()
    # Updating the peer connection inside the map
    pcs_map[answer["pc_id"]] = pipecat_connection

    return answer


@app.post("/api/compliance")
async def get_compliance_score(request: Request):
    body = await request.json()
    transcript = body.get("transcript", "")

    # Model
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18",
                       temperature=0.6,
                       max_tokens=None,
                       timeout=None,
                       max_retries=2)

    # Building the compliance checker prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         """You are a compliance checker for customer service transcripts. 
     Return a compliance score from 1 to 100 based on whether the agent asked all of the following questions (accept similar/related questions, not just exact wording):
 
     - Street address and Zip Code
     - Confirm City and State
     - First and Last Name
     - Do you rent or own?
     - Is the electricity in your name at this address?
     - If already in their name: Are the lights on?
 
     If any are missing, reduce the score proportionally. 
     Return your answer as a JSON object with keys: "score" (integer). I just need the score and no other explanation.
     """),
        ("user", "{input}")
    ])

    chain = prompt | model
    response = chain.invoke({"input": transcript})

    try:
        score = json.loads(response.content)['score']
        if isinstance(score, (int, float)):
            return score
        else:
            return 85
    except Exception:
        return 85


@app.post("/api/overall_score")
async def get_overall_score(request: Request):
    body = await request.json()
    transcript = body.get("transcript", "")

    # Model
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18",
                       temperature=0.6,
                       max_tokens=None,
                       timeout=None,
                       max_retries=2)

    # Building the compliance checker prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         """You are a call quality checker for customer service transcripts.
             Return a call quality score from 1 to 100 based on whether the agent did all of the following (accept similar/related actions, not just exact wording):
 
             Greeted the customer.
 
             Collected customer information.
 
             Answered the customer’s questions politely.
 
             Acknowledged and addressed the customer’s questions.
 
             Pitched the product to the customer.
 
             Closed the call and ended the call on a good note.
 
             If any are missing, reduce the score proportionally.
             Return your answer as a JSON object with the key: "score" (integer). I just need the score and no other explanation.
             """),
        ("user", "{input}")
    ])

    chain = prompt | model
    response = chain.invoke({"input": transcript})

    try:
        score = json.loads(response.content)['score']
        if isinstance(score, (int, float)):
            return score
        else:
            return 85
    except Exception:
        return 85


@app.post("/api/customer_satisfaction")
async def get_customer_satisfaction(request: Request):
    body = await request.json()
    transcript = body.get("transcript", "")

    # Model
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18",
                       temperature=0.6,
                       max_tokens=None,
                       timeout=None,
                       max_retries=2)

    # Building the compliance checker prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         """You are an evaluator tasked with rating customer satisfaction based on service call transcripts.
          Assign a customer satisfaction score from 1 to 5, where:
  
          5 = Extremely satisfied
  
          4 = Satisfied
  
          3 = Neutral
  
          2 = Dissatisfied
  
          1 = Extremely dissatisfied
  
          Base your score on tone, professionalism, helpfulness, and whether the customer’s needs were fully understood and resolved. 
          Look for signs of frustration or delight from the customer, and how effectively the agent handled the interaction overall.
          Return your result as a JSON object with the key: "score" (integer). Do not include any explanations or comments—just the score.
          """),
        ("user", "{input}")
    ])

    chain = prompt | model
    response = chain.invoke({"input": transcript})

    try:
        score = json.loads(response.content)['score']
        if isinstance(score, (int, float)):
            return score
        else:
            return 3
    except Exception:
        return 3


@app.post("/api/script_adherence")
async def get_script_adherence(request: Request):
    body = await request.json()
    transcript = body.get("transcript", "")

    # Model
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18",
                       temperature=0.6,
                       max_tokens=None,
                       timeout=None,
                       max_retries=2)

    # Building the compliance checker prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         """You are a script adherence evaluator for customer service transcripts.
          Return a score from 1 to 100 based on how closely the agent followed the expected call flow and maintained topic relevance. Evaluate the following:
  
          Greeting – The agent greeted the customer politely and naturally.
          Customer Info – The agent collected customer information and responded politely to provided details.
          Mandatory Questions – The agent asked required questions and responded politely to answers.
          Coupons & Discounts – The agent acknowledged any discounts or coupons appreciatively.
          SOE Value Statement / Credit – The agent acknowledged this in a way tailored to the customer’s setting.
          Pitch – The agent acknowledged the context and pitched the offering while creating relevant hesitation, politely.
          Close / Overcoming Hesitation – The agent appreciated the customer’s engagement, addressed any hesitations sincerely, and closed the call naturally.
          Topic Relevance – The agent stayed focused on the reason the customer reached out (e.g., discussing energy plans if the customer inquired about that), and did not diverge into unrelated topics (e.g., selling unrelated products like burgers).
  
          If any step is missed or done poorly, deduct points proportionally.
          Return the result as a JSON object with the key: "score" (integer, 1–100). Do not include explanations—just the score.
          """),
        ("user", "{input}")
    ])

    chain = prompt | model
    response = chain.invoke({"input": transcript})

    try:
        score = json.loads(response.content)['score']
        if isinstance(score, (int, float)):
            return score
        else:
            return 70
    except Exception:
        return 70


@app.post("/api/hesitation")
async def get_hesitation_score(request: Request):
    body = await request.json()
    transcript = body.get("transcript", "")

    # Model
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18",
                       temperature=0.8,
                       max_tokens=None,
                       timeout=None,
                       max_retries=2)

    # Building the compliance checker prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         """You are an evaluator assessing an agent’s ability to handle hesitation in a customer service transcript.
     Return a score from 1 to 100 based on the agent’s effectiveness in managing hesitation moments during the conversation.
 
     Handling Hesitation includes:
 
     Responding confidently and fluidly, without long pauses or awkward transitions.
 
     Proactively addressing customer doubts, uncertainty, or objections with reassurance.
 
     Maintaining a steady, calm, and composed tone even when the customer is unsure.
 
     Minimizing signs of confusion, delay, or indecision from the agent.
 
     Helping reduce customer uncertainty and guiding them toward a decision.
 
     Deduct points if the agent hesitates, shows signs of uncertainty, fails to resolve customer doubts, or causes more confusion.
     Reward high scores for smooth, confident handling, even in difficult parts of the call.
 
     Return your answer as a JSON object with the key: "score" (integer, 1–100). No other explanation is needed.
     """),
        ("user", "{input}")
    ])

    chain = prompt | model
    response = chain.invoke({"input": transcript})

    try:
        score = json.loads(response.content)['score']
        if isinstance(score, (int, float)):
            return score
        else:
            return 70
    except Exception:
        return 70


@app.post("/api/feedback")
async def get_feedback(transcript: str = Body(..., embed=True)):
    # Model
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18",
                       temperature=0.8,
                       max_tokens=None,
                       timeout=None,
                       max_retries=2)

    # Building the compliance checker prompt
    prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a customer-service call evaluator.

Task
1. Read the transcript provided by the user.
2. Assess the agent in four categories:
   • compliance: Did the agent ask required questions like name, address, city/state, electricity status, etc.?
   • call_quality: Did the agent greet, collect info, answer politely, pitch, and close professionally?
   • customer_satisfaction: Was the customer’s tone positive, and were their needs understood and resolved effectively?
   • handling_hesitation: Did the agent respond confidently and reduce customer uncertainty without sounding unsure or pausing?

Output
Return a JSON array that contains EXACTLY five (5) objects.
Each object must include:
  "category" – one of the four category names above (snake_case)
  "feedback" – ONE actionable sentence (≤ 20 words) that ends with a newline character

Rules
• Output only the JSON array – no extra text before or after it.  
• Do NOT include scores, numbers, or long explanations.  
• Do not repeat the same words or ideas across sentences.  
• The JSON must be valid.

Example (double braces are used only to escape literal braces):
[
{{  
  "category": "compliance",
  "feedback": "Always verify the customer's service address to meet regulatory requirements."
}},
...
]
"""
    ),
    ("user", "{input}")
])
    chain = prompt | model
    response = chain.invoke({"input": transcript})

    default_feedback = """
    Please ensure all required questions are asked to stay compliant with the call script.\n
    Maintain a natural flow from greeting to closing for better overall call quality.\n
    Make sure the customer feels heard and their concerns are fully addressed.\n
    Speak confidently and avoid pauses to reduce customer hesitation and build trust.\n
    Keep the conversation relevant and focused on the customer’s original reason for calling.\n
    """

    try:
        raw_feedback = response.content.strip()

        # 1️⃣ normal case – valid JSON already
        feedback = json.loads(raw_feedback)
        return feedback

    except (json.JSONDecodeError, TypeError, ValueError):
        # 2️⃣ the model might use single-quotes → quick fix then retry
        try:
            feedback = json.loads(raw_feedback.replace("'", '"'))
            return feedback
        except Exception:
            # 3️⃣ still not valid → fall back to default text
            return default_feedback.strip()

    except Exception:
        return default_feedback.strip()


@app.get("/")
async def serve_index():
    return FileResponse("index.html")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # Run app
    coros = [pc.disconnect() for pc in pcs_map.values()]
    await asyncio.gather(*coros)
    pcs_map.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebRTC demo")
    parser.add_argument(
        "--host", default="localhost", help="Host for HTTP server (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=7860, help="Port for HTTP server (default: 7860)"
    )
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    logger.remove(0)
    if args.verbose:
        logger.add(sys.stderr, level="TRACE")
    else:
        logger.add(sys.stderr, level="DEBUG")

    uvicorn.run(app, host=args.host, port=args.port)
