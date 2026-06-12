import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import "./i18n";
import "./index.css";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Interactions from "./pages/Interactions";
import DBPerformance from "./pages/DBPerformance";
import NLPAnalysis from "./pages/NLPAnalysis";
import Results from "./pages/Results";
import Presentation from "./pages/presentation/Presentation";
import DataExplorer from "./pages/DataExplorer";

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/presentation" element={<Presentation />} />
          <Route path="/data-explorer" element={<DataExplorer />} />
          <Route path="/interactions" element={<Interactions />} />
          <Route path="/database-performance" element={<DBPerformance />} />
          <Route path="/nlp-analysis" element={<NLPAnalysis />} />

          {/* kept reachable but no longer in the main nav */}
          <Route path="/results" element={<Results />} />
          {/* legacy catalogue routes → redirect into the Data Explorer */}
          <Route path="/medications" element={<Navigate to="/data-explorer" replace />} />
          <Route path="/active-ingredients" element={<Navigate to="/data-explorer" replace />} />
          <Route path="/laboratories" element={<Navigate to="/data-explorer" replace />} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
