import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function RequirementInput() {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [repoId, setRepoId] = useState('');
  const [priority, setPriority] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE}/requirements`, {
        text,
        repo_id: repoId,
        priority,
        source: 'manual',
      });

      // If there are ambiguities, show them
      if (response.data.ambiguities.length > 0) {
        // Navigate to ambiguity resolution
        navigate(`/requirements/${response.data.req_id}/ambiguities`);
      } else {
        // Navigate to plan review
        navigate(`/requirements/${response.data.req_id}/plan`);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to submit requirement');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold">Submit Requirement</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">
              Repository
            </label>
            <select
              value={repoId}
              onChange={(e) => setRepoId(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:border-blue-500"
              required
            >
              <option value="">Select a repository</option>
              <option value="owner/repo">owner/repo</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:border-blue-500"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Requirement Description
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 h-48 focus:outline-none focus:border-blue-500 font-mono text-sm"
              placeholder="Describe what you want to implement...

Example:
Add rate limiting to the /api/users endpoint.
- Maximum 100 requests per minute per IP
- Return 429 Too Many Requests when limit exceeded
- Include Retry-After header"
              required
            />
          </div>

          {error && (
            <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-400">
              {error}
            </div>
          )}

          <div className="flex gap-4">
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 px-6 py-3 rounded-lg font-medium transition-colors"
            >
              {loading ? 'Processing...' : 'Submit Requirement'}
            </button>
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="bg-gray-700 hover:bg-gray-600 px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>

        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h3 className="font-semibold mb-4">Tips for writing requirements</h3>
          <ul className="text-gray-400 space-y-2 text-sm">
            <li>• Be specific about what you want to achieve</li>
            <li>• Include acceptance criteria when possible</li>
            <li>• Mention any performance or security requirements</li>
            <li>• Reference existing tickets or documentation</li>
          </ul>
        </div>
      </main>
    </div>
  );
}

export default RequirementInput;
