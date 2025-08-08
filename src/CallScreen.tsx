import {useState, useRef, useEffect} from "react";
import {useLocation, useNavigate} from "react-router-dom";
import {createClient} from "./lib/pipecat-client.ts";
import {analyzeCall} from "./lib/analyze-call.ts";

function CallScreen() {
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const [transcript, setTranscript] = useState<string[]>([]);
  const [client, setClient] = useState<any>(null);
  const [callAnalysis, setCallAnalysis] = useState<any>(null);
  const [botReady, setBotReady] = useState<any>(null);
  const [callStartTime, setCallStartTime] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [timerInterval, setTimerInterval] = useState<NodeJS.Timeout | null>(null);  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [analysisDone, setAnalysisDone] = useState(false);
  const [sentimentScore, setSentimentScore] = useState(50);

  const location = useLocation();
  const navigate = useNavigate();

  const persona = location.state?.persona || {};

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTo({
        top: transcriptRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [transcript]);

  const start = async () => {
    setConnecting(true);

    const c = createClient(
      persona,
      (text: string) => {
        setTranscript((p) => [...p, text]);
      },
      (track: MediaStreamTrack) => {
        const audioElement = document.createElement("audio");
        audioElement.srcObject = new MediaStream([track]);
        document.body.appendChild(audioElement);
        audioElement.play();
      },
      () => {
        setConnecting(false)
        setBotReady(true)
      },
      (score: number) => {
        setSentimentScore(score);
      }
    );

    await c.connect();
    setClient(c);
    setConnected(true);

    setCallStartTime(Date.now());
    const interval = setInterval(() => {
      setElapsedSeconds(prev => prev + 1);
    }, 1000);
    setTimerInterval(interval);
  };

  const stop = async () => {
    client?.disconnect();
    setConnected(false);
    setShowModal(true);

    if (timerInterval) {
      clearInterval(timerInterval);
    }
    setTimerInterval(null);

    const duration = Math.floor((Date.now() - (callStartTime || 0)) / 1000);

    const analysisResult = await analyzeCall(transcript, duration);
    console.log("Analysis result:", analysisResult); // optional debug

    setAnalysisDone(true);
    setCallAnalysis(analysisResult);
  };

  // void start();

  return (
    <div className="flex flex-1 gap-8 px-4 pt-4 pb-6 sm:px-6 lg:px-4 xl:px-2">
      {/* Left Panel */}
      <div className="flex-1 bg-white rounded-lg shadow p-6">
        <div className="mb-4 flex justify-between items-start">
          <h2 className="text-lg font-semibold">Call Transcript</h2>
          <div className="flex items-center gap-4">
            {(botReady !== null || connecting) && (
              <span
                className={`text-sm font-medium px-3 py-1 rounded-full ${
                  botReady ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                }`}
              >
              {connecting ? 'Connecting...' : botReady ? 'Ready to speak' : ''}
              </span>
            )}
            <div className="flex gap-2">
              <button
                onClick={start}
                className="bg-blue-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={connected || connecting || botReady}
              >
                {connected || connecting || botReady ? "Call Started" : "Start"}
              </button>
              <button
                onClick={stop}
                className="bg-red-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!connected}
              >
                End
              </button>
            </div>
          </div>
        </div>

        <div
          className="overflow-y-auto bg-gray-50 p-4 rounded text-sm border space-y-2 transition-all"
          style={{ maxHeight: '20rem', minHeight: '40rem' }}
          ref={transcriptRef}
        >
          {transcript.length === 0 ? (
            <p className="text-gray-400">No transcript yet...</p>
          ) : (
            transcript.map((line, i) => {
              const isAgent = line.startsWith("Agent:");
              const message = line.replace(/^Agent:\s?|^Customer:\s?/, "");
              const label = isAgent ? "Agent" : "Customer";

              return (
                <div key={i} className={`flex ${isAgent ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-xs px-4 py-2 rounded-lg relative ${
                      isAgent
                        ? "bg-blue-600 text-white rounded-br-none"
                        : "bg-white text-gray-900 border border-gray-300 rounded-bl-none"
                    }`}
                  >
                    <p className="text-xs font-semibold mb-1 text-gray-300 uppercase tracking-wide">
                      {label}
                    </p>
                    <p>{message}</p>
                  </div>
                </div>
              );
            })
          )}
        </div>

      </div>

      {/* Right Panel */}
      <aside className="w-[340px] shrink-0 bg-white rounded-lg shadow p-6">
        <h2 className="text-md font-semibold mb-4">Call Timer</h2>
        <div className="flex justify-between text-center text-sm mb-6">
          <div>
            <p className="font-semibold text-lg">
              {String(Math.floor(elapsedSeconds / 3600)).padStart(2, '0')}
            </p>
            <p className="text-gray-500">Hours</p>
          </div>
          <div>
            <p className="font-semibold text-lg">
              {String(Math.floor((elapsedSeconds % 3600) / 60)).padStart(2, '0')}
            </p>
            <p className="text-gray-500">Minutes</p>
          </div>
          <div>
            <p className="font-semibold text-lg">
              {String(elapsedSeconds % 60).padStart(2, '0')}
            </p>
            <p className="text-gray-500">Seconds</p>
          </div>
        </div>


        <h3 className="text-md font-semibold mb-2">Customer Details</h3>
        <div className="text-center mb-4">
        <img
            src={persona.img}
            alt="Persona"
            className="w-20 h-20 mx-auto rounded-full mb-2"
          />
          <h4 className="font-semibold">{persona.title}</h4>
        </div>
        <div className="text-sm text-gray-600 space-y-2 mb-4">
          <p><strong>Address:</strong> {persona.address}</p>
          <p><strong>Birth Date:</strong> {persona.birthDate}</p>
          <p><strong>Email:</strong> {persona.email}</p>
          <p><strong>Rent or Own:</strong> {persona.ownership}</p>
          <p><strong>Language:</strong> {persona.language}</p>
        </div>

        <h2 className="text-md font-semibold mb-4">Customer Sentiment</h2>

        <div className="w-full mt-2">
          {/* Sentiment Bar */}
          <div className="relative h-4 w-full rounded-full bg-gradient-to-r from-red-500 via-yellow-400 to-green-500">
            {/* Indicator (adjust left % based on sentiment score) */}
            <div
              className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-gray-800"
              style={{ left: `${sentimentScore}%` }}
            />
          </div>

            {/* Label under the bar */}
            <div className="mt-1 text-sm text-gray-600 flex justify-between">
              <span>
                {sentimentScore >= 66
                  ? "Positive"
                  : sentimentScore >= 33
                    ? "Neutral"
                    : "Negative"}
              </span>
            </div>
        </div>


        <div className="mt-6">
          <h3 className="text-md font-semibold mb-1">Notes</h3>
          <textarea
            placeholder="Add notes about the customer interaction"
            className="w-full h-20 p-2 border rounded text-sm"
          />
        </div>
      </aside>
      <audio id="bot-audio" autoPlay/>

      {/** Analysis model **/}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-8 text-center max-w-sm w-full">
            <h2 className="text-xl font-semibold mb-4">
              {analysisDone ? "Analysis Complete" : "Analyzing your call..."}
            </h2>

            <p className="text-gray-600 mb-6">
              {analysisDone
                ? "Your call review is ready. Click below to see your results."
                : "We’re reviewing your performance. This should only take a moment."}
            </p>

            {analysisDone ? (
              <button
                onClick={() => navigate('/call-analysis', { state: { callAnalysis } })}
                className="button_primary w-full"
              >
                View Results
              </button>
            ) : (
              <div className="flex justify-center">
                <svg className="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none"
                     viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}

export default CallScreen;
