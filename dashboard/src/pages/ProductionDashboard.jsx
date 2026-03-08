import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function ProductionDashboard() {
  const [deployments, setDeployments] = useState([]);
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    loadDeployments();
    const interval = setInterval(loadDeployments, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDeployments = async () => {
    try {
      // Mock data - in production, fetch from API
      setDeployments([
        {
          id: 'deploy-1',
          environment: 'production',
          status: 'deployed',
          health: 'healthy',
          deployed_at: '2024-01-15T10:30:00Z',
        },
      ]);

      setMetrics({
        error_rate: 0.02,
        p99_latency: 145,
        requests_per_second: 1234,
        active_users: 567,
      });
    } catch (err) {
      console.error('Failed to load deployments:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold">Production Dashboard</h1>
          <p className="text-gray-400">Real-time production monitoring</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Metrics */}
        {metrics && (
          <div className="grid grid-cols-4 gap-4 mb-6">
            <MetricCard
              label="Error Rate"
              value={`${metrics.error_rate}%`}
              trend="down"
              good={metrics.error_rate < 1}
            />
            <MetricCard
              label="P99 Latency"
              value={`${metrics.p99_latency}ms`}
              trend="stable"
              good={metrics.p99_latency < 200}
            />
            <MetricCard
              label="Requests/sec"
              value={metrics.requests_per_second.toLocaleString()}
              trend="up"
            />
            <MetricCard
              label="Active Users"
              value={metrics.active_users.toLocaleString()}
              trend="up"
            />
          </div>
        )}

        {/* Deployments */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Active Deployments</h2>
          <div className="space-y-4">
            {deployments.map((dep) => (
              <DeploymentRow key={dep.id} deployment={dep} />
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
          <div className="space-y-3">
            <ActivityItem
              type="deploy"
              message="Deployed to production"
              time="2 hours ago"
            />
            <ActivityItem
              type="repair"
              message="Self-repair completed successfully"
              time="5 hours ago"
            />
            <ActivityItem
              type="alert"
              message="Latency spike detected (resolved)"
              time="1 day ago"
            />
          </div>
        </div>
      </main>
    </div>
  );
}

function MetricCard({ label, value, trend, good }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex justify-between items-start mb-2">
        <span className="text-sm text-gray-400">{label}</span>
        {trend && (
          <span className={`text-xs ${
            trend === 'up' ? 'text-green-400' :
            trend === 'down' ? 'text-red-400' :
            'text-gray-400'
          }`}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
          </span>
        )}
      </div>
      <div className={`text-2xl font-bold ${good === false ? 'text-red-400' : ''}`}>
        {value}
      </div>
    </div>
  );
}

function DeploymentRow({ deployment }) {
  return (
    <div className="flex justify-between items-center p-4 bg-gray-900 rounded">
      <div className="flex items-center gap-4">
        <span className={`w-3 h-3 rounded-full ${
          deployment.health === 'healthy' ? 'bg-green-500' :
          deployment.health === 'degraded' ? 'bg-yellow-500' :
          'bg-red-500'
        }`} />
        <div>
          <div className="font-medium">{deployment.environment}</div>
          <div className="text-sm text-gray-400">{deployment.id}</div>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span className={`px-2 py-1 rounded text-sm ${
          deployment.status === 'deployed' ? 'bg-green-900 text-green-400' :
          deployment.status === 'deploying' ? 'bg-blue-900 text-blue-400' :
          'bg-red-900 text-red-400'
        }`}>
          {deployment.status}
        </span>
        <span className="text-sm text-gray-400">
          {new Date(deployment.deployed_at).toLocaleString()}
        </span>
      </div>
    </div>
  );
}

function ActivityItem({ type, message, time }) {
  const icons = {
    deploy: '🚀',
    repair: '🔧',
    alert: '⚠️',
  };

  return (
    <div className="flex items-center gap-3">
      <span className="text-xl">{icons[type]}</span>
      <span className="flex-1">{message}</span>
      <span className="text-sm text-gray-400">{time}</span>
    </div>
  );
}

export default ProductionDashboard;
