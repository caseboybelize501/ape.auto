import React from 'react';
import { useParams } from 'react-router-dom';

function PRReview() {
  const { runId } = useParams();

  // Mock PR data
  const pr = {
    pr_number: 42,
    title: 'APE: Add rate limiting to /api/users',
    pr_url: 'https://github.com/owner/repo/pull/42',
    files_changed: [
      'src/api/users.py',
      'src/middleware/rate_limiter.py',
      'tests/test_rate_limiter.py',
    ],
    additions: 156,
    deletions: 12,
    ci_status: 'success',
    tests: {
      regression: 'passed',
      contract: 'passed',
      acceptance: 'passed',
    },
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold">GATE-2: PR Review</h1>
          <p className="text-gray-400">Review generated code before merge</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* PR Info */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-lg font-semibold">{pr.title}</h2>
              <a
                href={pr.pr_url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-400 hover:text-blue-300"
              >
                View on GitHub →
              </a>
            </div>
            <span className="px-3 py-1 bg-blue-900 text-blue-400 rounded-full text-sm">
              PR #{pr.pr_number}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-400">Files Changed</div>
              <div className="text-xl font-medium">{pr.files_changed.length}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Additions</div>
              <div className="text-xl font-medium text-green-400">+{pr.additions}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Deletions</div>
              <div className="text-xl font-medium text-red-400">-{pr.deletions}</div>
            </div>
          </div>
        </div>

        {/* CI/CD Status */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h3 className="font-semibold mb-4">CI/CD Status</h3>
          <div className="flex items-center gap-2 mb-4">
            <span className="w-3 h-3 rounded-full bg-green-500"></span>
            <span className="text-green-400">All checks passed</span>
          </div>
          <div className="space-y-2">
            <TestResult name="Regression Guards" status={pr.tests.regression} />
            <TestResult name="Contract Tests" status={pr.tests.contract} />
            <TestResult name="Acceptance Tests" status={pr.tests.acceptance} />
          </div>
        </div>

        {/* Files */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h3 className="font-semibold mb-4">Files Changed</h3>
          <ul className="space-y-2">
            {pr.files_changed.map((file, i) => (
              <li key={i} className="flex items-center gap-2 font-mono text-sm">
                <span className="text-green-400">M</span>
                {file}
              </li>
            ))}
          </ul>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-medium transition-colors">
            Approve & Deploy to Staging
          </button>
          <button className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-medium transition-colors">
            Request Changes
          </button>
        </div>
      </main>
    </div>
  );
}

function TestResult({ name, status }) {
  return (
    <div className="flex justify-between items-center p-3 bg-gray-900 rounded">
      <span>{name}</span>
      <span className={`px-2 py-1 rounded text-sm ${
        status === 'passed' ? 'bg-green-900 text-green-400' : 'bg-red-900 text-red-400'
      }`}>
        {status.toUpperCase()}
      </span>
    </div>
  );
}

export default PRReview;
