import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API_BASE = 'http://localhost:8000/api';

function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [period, setPeriod] = useState('month');

  useEffect(() => {
    loadAnalytics();
  }, [period]);

  const loadAnalytics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/analytics?period=${period}`);
      setAnalytics(response.data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    }
  };

  if (!analytics) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-xl">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-gray-400">Usage metrics and statistics</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Period Selector */}
        <div className="flex gap-4 mb-6">
          {['day', 'week', 'month', 'year'].map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                period === p
                  ? 'bg-blue-600'
                  : 'bg-gray-800 hover:bg-gray-700'
              }`}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <StatCard label="Total Runs" value={analytics.total_runs} />
          <StatCard label="Success Rate" value={`${(analytics.successful_runs / analytics.total_runs * 100).toFixed(0)}%`} />
          <StatCard label="Avg Cycle Time" value={`${analytics.average_cycle_time_minutes}m`} />
          <StatCard label="Deployments" value={analytics.deployments} />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Critic Pass Rates */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="font-semibold mb-4">Critic Pass Rates</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={[
                { name: 'Syntax', rate: analytics.critic_pass_rates.pass1_syntax * 100 },
                { name: 'Contract', rate: analytics.critic_pass_rates.pass2_contract * 100 },
                { name: 'Completeness', rate: analytics.critic_pass_rates.pass3_completeness * 100 },
                { name: 'Logic', rate: analytics.critic_pass_rates.pass4_logic * 100 },
              ]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip />
                <Bar dataKey="rate" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Requirements by Source */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="font-semibold mb-4">Requirements by Source</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={[
                { name: 'Manual', count: analytics.requirements_by_source.manual },
                { name: 'Ticket', count: analytics.requirements_by_source.ticket },
                { name: 'PRD', count: analytics.requirements_by_source.prd },
                { name: 'Voice', count: analytics.requirements_by_source.voice },
              ]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip />
                <Bar dataKey="count" fill="#10B981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Affected Modules */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="font-semibold mb-4">Top Affected Modules</h3>
          <div className="space-y-3">
            {analytics.top_affected_modules.map((mod, i) => (
              <div key={i} className="flex justify-between items-center">
                <span className="font-mono text-sm">{mod.path}</span>
                <span className="text-blue-400">{mod.changes} changes</span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-sm text-gray-400 mb-1">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

export default Analytics;
