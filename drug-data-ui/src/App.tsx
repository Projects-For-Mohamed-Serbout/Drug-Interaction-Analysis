import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import "./i18n";
import "./index.css";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Medications from "./pages/Medications";
import Interactions from "./pages/Interactions";
import ActiveIngredients from "./pages/ActiveIngredients";
import Laboratories from "./pages/Laboratories";
import DBPerformance from "./pages/DBPerformance";
import NLPAnalysis from "./pages/NLPAnalysis";

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/medications" element={<Medications />} />
          <Route path="/interactions" element={<Interactions />} />
          <Route path="/active-ingredients" element={<ActiveIngredients />} />
          <Route path="/laboratories" element={<Laboratories />} />
          <Route path="/database-performance" element={<DBPerformance />} />
          <Route path="/nlp-analysis" element={<NLPAnalysis />} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
