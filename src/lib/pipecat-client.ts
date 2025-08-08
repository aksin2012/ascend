import {PipecatClient} from "@pipecat-ai/client-js";
import {SmallWebRTCTransport} from "@pipecat-ai/small-webrtc-transport";

export function createClient(
  persona: { id: string } ,
  onTranscript: (text: string) => void,
  onAudio: (track: MediaStreamTrack) => void,
  onBotReady: () => void,
  onSentimentAnalysis: (score: number) => void
) {
  const transport = new SmallWebRTCTransport({
    connectionUrl: `http://localhost:7860/api/offer?persona=${persona.id}`,
    audioCodec: 'default'
  });

  return new PipecatClient({
    transport,
    enableMic: true,
    enableCam: false,
    callbacks: {
      onBotReady: () => onBotReady(),
      onUserStartedSpeaking: () => {
        console.log('onUserStartedSpeaking');
      },
      onBotTranscript: (msg) => {
        onTranscript(`Customer: ${msg.text}`);
      },
      onUserTranscript: (msg) => {
        if (msg.final) {
          onTranscript(`Agent: ${msg.text}`);
        }
      },
      onTrackStarted: (track: MediaStreamTrack, participant) => {
        if (participant?.local) {
          return;
        }
        onAudio(track);
      },
      onServerMessage: (data) => {
        console.log('new server message', data);

        if (data.type === 'sentiment-analysis') {
          onSentimentAnalysis(data.sentiment);
        }
      },
      onError: (err) => console.error("Client error:", err),
    },
  });
}
