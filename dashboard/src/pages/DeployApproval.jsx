import React from 'react';
import { useParams } from 'react-router-dom';

function DeployApproval() {
  const { deploymentId } = useParams();

  // Mock deployment data
  const deployment = {
    id: deploymentId,
    environment: 'staging',
    status: 'deployed',
    health: 'healthy',
    url: 'https://staging.example.com',
    metrics: {
      error_rate: '0.02%',
      p99_latency: '145ms',
      requests_per_second: '1,234',
    },
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold">GATE-3: Deploy Approval</h1>
          <p className="text-gray-400">Review staging deployment before production</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Staging Info */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-lg font-semibold">Staging Deployment</h2>
              <a
                href={deployment.url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-400 hover:text-blue-300"
              >
                {deployment.url} →
              </a>
            </div>
            <span className="px-3 py-1 bg-green-900 text-green-400 rounded-full text-sm">
              {deployment.status.toUpperCase()}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-green-500"></span>
            <span className="text-green-400">Health: {deployment.health}</span>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <MetricCard label="Error Rate" value={deployment.metrics.error_rate} />
          <MetricCard label="P99 Latency" value={deployment.metrics.p99_latency} />
          <MetricCard label="Requests/sec" value={deployment.metrics.requests_per_second} />
        </div>

        {/* Smoke Tests */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h3 className="font-semibold mb-4">Smoke Tests</h3>
          <div className="space-y-2">
            <SmokeTest name="GET /health" status="passed" duration="45ms" />
            <SmokeTest name="GET /api/users" status="passed" duration="123ms" />
            <SmokeTest name="POST /api/users" status="passed" duration="234ms" />
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-medium transition-colors">
            Approve Production Deploy
          </button>
          <button className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-medium transition-colors">
            Reject - Rollback
          </button>
        </div>
      </main>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-sm text-gray-400 mb-1">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

function SmokeTest({ name, status, duration }) {
  return (
    <div className="flex justify-between items-center p-3 bg-gray-900 rounded">
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-green-500"></span>
        <span className="font-mono text-sm">{name}</span>
      </div>
      <span className="text-sm text-gray-400">{duration}</span>
    </div>
  );
}

export default DeployApproval;
