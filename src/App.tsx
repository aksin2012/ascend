import { Routes, Route } from 'react-router-dom';
import ChoosePersonaScreen from './ChoosePersona';
import CallAnalysisScreen from "./CallAnalysisScreen.tsx";
import CallScreen from "./CallScreen.tsx";

function App() {
  return (
    <Routes>
      <Route path="/" element={<ChoosePersonaScreen />} />
      <Route path="/call" element={<CallScreen />} />
      <Route path="/call-analysis" element={<CallAnalysisScreen />} />
    </Routes>
  );
}

export default App;
