import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import RequirementInput from './pages/RequirementInput';
import PlanReview from './pages/PlanReview';
import GenerationProgress from './pages/GenerationProgress';
import CriticLog from './pages/CriticLog';
import HaltReport from './pages/HaltReport';
import PRReview from './pages/PRReview';
import DeployApproval from './pages/DeployApproval';
import ProductionDashboard from './pages/ProductionDashboard';
import Analytics from './pages/Analytics';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/requirements/new" element={<RequirementInput />} />
        <Route path="/requirements/:reqId/plan" element={<PlanReview />} />
        <Route path="/generations/:runId" element={<GenerationProgress />} />
        <Route path="/generations/:runId/critic/:level" element={<CriticLog />} />
        <Route path="/generations/:runId/halt" element={<HaltReport />} />
        <Route path="/prs/:runId" element={<PRReview />} />
        <Route path="/deployments/:deploymentId" element={<DeployApproval />} />
        <Route path="/production" element={<ProductionDashboard />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
