import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

function CallAnalysisScreen() {
  const navigate = useNavigate();
  const location = useLocation();
  const callAnalysis = location.state?.callAnalysis;

  const [complianceScore, setComplianceScore] = useState(0);
  const [overallScore, setOverallScore] = useState(0);
  const [scriptAdherenceScore, setScriptAdherenceScore] = useState(0);
  const [hesitationScore, setHesitationScore] = useState(0);
  const [customerSatisfactionScore, setCustomerSatisfactionScore] = useState(0);
  const [feedback, setFeedback] = useState([]);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    if (callAnalysis) {
      setComplianceScore(Number(callAnalysis.compliance));
      setOverallScore(Number(callAnalysis.overall_score));
      setScriptAdherenceScore(Number(callAnalysis.script_adherence));
      setHesitationScore(Number(callAnalysis.hesitation));
      setCustomerSatisfactionScore(Number(callAnalysis.customer_satisfaction));
      setFeedback(callAnalysis.feedback);
      setDuration(Number(callAnalysis.duration));
    }
  }, [callAnalysis]);

  const formatDuration = (seconds: any) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins} min ${secs} sec`;
  };

  return (
    <div className="flex justify-center px-4 pt-6 pb-12 sm:px-6 lg:px-8">
      <div className="max-w-screen-xl w-full flex flex-col gap-8">

        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">📊 Call Performance Summary</h1>
          <button onClick={() => navigate('/')} className="button_primary">
            Start New Call
          </button>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Call Duration */}
          <div className="card">
            <h2 className="typography_h2 mb-2">Call Duration</h2>
            <div className="flex justify-between items-center mb-2">
              <p className="text-lg font-semibold text-gray-800">{formatDuration(duration)}</p>
              <span className="text-sm text-gray-500">Industry Avg: 5:30</span>
            </div>
            <p className="typography_body mt-2">Compared to 5:30 industry average. Shorter calls can improve handle time
              but may affect quality.</p>
          </div>

          {/* Overall Score */}
          <div className="card">
            <h2 className="typography_h2 mb-2">Overall Score</h2>
            <div className="flex justify-between items-center mb-2">
              <p className="text-lg font-semibold text-indigo-600">{overallScore}%</p>
              <span className="text-sm text-gray-500">Industry Avg: 74%</span>
            </div>
            <div className="relative h-4 w-full rounded-full bg-gradient-to-r from-red-500 via-yellow-400 to-green-500">
              <div className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-gray-800"
                   style={{ left: `${overallScore}%` }}/>
            </div>
            <p className="typography_body mt-2">Well above average for your industry peers based on total performance
              metrics.</p>
          </div>

          {/* Compliance */}
          <div className="card">
            <h2 className="typography_h2 mb-2">Compliance</h2>
            <div className="flex justify-between items-center mb-2">
              <p className="text-lg font-semibold text-green-600">{complianceScore}%</p>
              <span className="text-sm text-gray-500">Target: 95%</span>
            </div>
            <div className="relative h-4 w-full rounded-full bg-gradient-to-r from-red-500 via-yellow-400 to-green-500">
              <div className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-gray-800"
                   style={{ left: `${complianceScore}%` }}/>
            </div>
            <p className="typography_body mt-2">You followed all required steps and disclosures during the call.</p>
          </div>

          {/* Customer Satisfaction */}
          <div className="card">
            <h2 className="typography_h2 mb-2">Customer Satisfaction</h2>
            <div className="flex justify-between items-center mb-2">
              <p className="text-lg font-semibold text-blue-600">{customerSatisfactionScore} / 5</p>
              <span className="text-sm text-gray-500">Industry Avg: 4.1</span>
            </div>
            <div className="relative h-4 w-full rounded-full bg-gradient-to-r from-red-500 via-yellow-400 to-green-500">
              <div className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-gray-800"
                   style={{ left: `${(customerSatisfactionScore / 5) * 100}%` }}/>
            </div>
            <p className="typography_body mt-2">Based on sentiment and tone detection.</p>
          </div>


          {/* Hesitation Handling */}
          <div className="card">
            <h2 className="typography_h2 mb-2">Hesitation Handling</h2>
            <div className="flex justify-between items-center mb-2">
              <p className="text-lg font-semibold text-indigo-600">{hesitationScore}%</p>
              <span className="text-sm text-gray-500">Industry Avg: 72%</span>
            </div>
            <div className="relative h-4 w-full rounded-full bg-gradient-to-r from-red-500 via-yellow-400 to-green-500">
              <div className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-gray-800"
                   style={{ left: `${hesitationScore}%` }}/>
            </div>
            <p className="typography_body mt-2">Measures how effectively the agent responded to hesitation, objections,
              or uncertainty.</p>
          </div>

          {/* Script Adherence */}
          <div className="card">
            <h2 className="typography_h2 mb-2">Script Adherence</h2>
            <div className="flex justify-between items-center mb-2">
              <p className="text-lg font-semibold text-purple-600">{scriptAdherenceScore}%</p>
              <span className="text-sm text-gray-500">Target: 90%</span>
            </div>
            <div className="relative h-4 w-full rounded-full bg-gradient-to-r from-red-500 via-yellow-400 to-green-500">
              <div className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-gray-800"
                   style={{ left: `${scriptAdherenceScore}%` }}/>
            </div>
            <p className="typography_body mt-2">Indicates how closely the agent followed the call script, including
              required phrases and compliance steps.</p>
          </div>
        </div>

        {/* Feedback */}
        <div className="card">
          <h2 className="typography_h2 mb-2">Observations</h2>
          <ul className="text-sm text-gray-700 list-disc list-inside space-y-2">
            {feedback?.map(({ category, feedback: comment }: any, index) => {
              const formatCategory = (raw: string) => {
                if (raw.includes("_")) {
                  return raw
                    .split("_")
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(" ");
                }
                if (raw === raw.toLowerCase()) {
                  return raw.charAt(0).toUpperCase() + raw.slice(1);
                }
                return raw;
              };

              return (
                <li key={index}>
                  <strong className="text-blue-600">{formatCategory(category)}:</strong> {comment.trim()}
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default CallAnalysisScreen;
