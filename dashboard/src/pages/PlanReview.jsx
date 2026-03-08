import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function PlanReview() {
  const { reqId } = useParams();
  const navigate = useNavigate();
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    loadPlan();
  }, [reqId]);

  const loadPlan = async () => {
    try {
      const response = await axios.get(`${API_BASE}/plans/${reqId}`);
      setPlan(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load plan');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    try {
      const response = await axios.post(`${API_BASE}/plans/${reqId}/approve`, {
        approved: true,
        notes,
      });

      // Navigate to generation progress
      navigate(`/generations/${response.data.run_id}`);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to approve plan');
    }
  };

  const handleReject = async () => {
    try {
      await axios.post(`${API_BASE}/plans/${reqId}/approve`, {
        approved: false,
        notes,
      });
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to reject plan');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-xl">Loading architecture plan...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-8">
        <div className="text-red-400">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold">GATE-1: Plan Review</h1>
          <p className="text-gray-400">Review architecture plan and contracts</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Architecture Summary */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Architecture Summary</h2>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm text-gray-400 mb-2">Modified Modules</h3>
              <ul className="space-y-1">
                {plan.modified_modules?.map((mod, i) => (
                  <li key={i} className="text-sm font-mono text-yellow-400">
                    {mod.path}
                  </li>
                ))}
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm text-gray-400 mb-2">New Modules</h3>
              <ul className="space-y-1">
                {plan.new_modules?.map((mod, i) => (
                  <li key={i} className="text-sm font-mono text-green-400">
                    {mod.path}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Risk Flags */}
        {plan.risk_flags?.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4 text-yellow-400">Risk Flags</h2>
            <ul className="space-y-3">
              {plan.risk_flags.map((risk, i) => (
                <li key={i} className="flex gap-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    risk.level === 'critical' ? 'bg-red-900 text-red-400' :
                    risk.level === 'high' ? 'bg-orange-900 text-orange-400' :
                    'bg-yellow-900 text-yellow-400'
                  }`}>
                    {risk.level.toUpperCase()}
                  </span>
                  <span>{risk.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Contracts */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Contracts (Immutable after approval)</h2>
          <p className="text-gray-400 text-sm mb-4">
            These contracts define the interface specifications. Once approved, they cannot be modified
            by the critic or repair loop.
          </p>
          <div className="bg-gray-900 rounded p-4 font-mono text-sm overflow-auto max-h-64">
            <pre>
{`# contracts/interfaces/pipeline.py

def process_user_data(user_id: str, data: dict) -> ProcessResult:
    """Process user data according to FR-001, FR-002"""
    ...

def validate_input(data: dict) -> ValidationResult:
    """Validate input according to NFR-001 (security)"""
    ...`}
            </pre>
          </div>
        </div>

        {/* Notes */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Review Notes (Optional)</h2>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 h-24 focus:outline-none focus:border-blue-500"
            placeholder="Add any notes or concerns..."
          />
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button
            onClick={handleApprove}
            className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Approve & Start Generation
          </button>
          <button
            onClick={handleReject}
            className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Reject Plan
          </button>
        </div>
      </main>
    </div>
  );
}

export default PlanReview;
