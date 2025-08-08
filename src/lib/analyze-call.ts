async function runAnalysis(endpoint: string, transcript: string) {
  try {
    const response = await fetch(`http://localhost:7860/api/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        transcript,
      })
    });

    if (!response.ok) throw new Error('Failed to analyze call');

    const score =  await response.text();

    return { name: endpoint, score };
  } catch (error) {
    console.error('Analysis error:', error);
    return null;
  }
}

async function getComplianceAnalysis(transcript: string[]) {
  return runAnalysis('compliance', transcript.join("\n"));
}

async function getOverallScore(transcript: string[]) {
  return runAnalysis('overall_score', transcript.join("\n"));
}

async function getCustomerSatisfaction(transcript: string[]) {
  return runAnalysis('customer_satisfaction', transcript.join("\n"));
}

async function getScriptAdherence(transcript: string[]) {
  return runAnalysis('script_adherence', transcript.join("\n"));
}

async function getHesitation(transcript: string[]) {
  return runAnalysis('hesitation', transcript.join("\n"));
}

async function getFeedback(transcript: string[]) {
  return runAnalysis('feedback', transcript.join("\n"));
}

export async function analyzeCall(transcript: string[], duration: number) {
  const results = await Promise.all([
    getComplianceAnalysis(transcript),
    getCustomerSatisfaction(transcript),
    getOverallScore(transcript),
    getScriptAdherence(transcript),
    getHesitation(transcript),
  ]);

  const feedback = await getFeedback(transcript)

  const scores = Object.fromEntries(
    results.map(r => [r!.name, r!.score])
  );

  return {
    ...scores,
    feedback: JSON.parse(feedback!.score),
    duration
  };
}
