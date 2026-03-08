import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function GenerationProgress() {
  const { runId } = useParams();
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProgress();
    const interval = setInterval(loadProgress, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [runId]);

  const loadProgress = async () => {
    try {
      const response = await axios.get(`${API_BASE}/generations/${runId}`);
      setRun(response.data);
    } catch (err) {
      console.error('Failed to load progress:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !run) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-xl">Loading generation progress...</div>
      </div>
    );
  }

  const progress = run.progress || {};
  const progressPercent = progress.progress_percent || 0;

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold">Generation Progress</h1>
          <p className="text-gray-400">Run: {run.id}</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Progress Bar */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="flex justify-between mb-2">
            <span className="text-sm text-gray-400">Overall Progress</span>
            <span className="text-sm font-medium">{progressPercent.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-4">
            <div
              className="bg-blue-600 h-4 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <StatCard label="Current Level" value={progress.current_level} />
          <StatCard label="Total Levels" value={progress.total_levels} />
          <StatCard label="Files Generated" value={progress.files_generated} />
          <StatCard label="Files Passed" value={progress.files_passed} />
        </div>

        {/* Levels */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Levels</h2>
          <div className="space-y-4">
            {Array.from({ length: progress.total_levels }).map((_, i) => (
              <LevelRow
                key={i}
                level={i}
                currentLevel={progress.current_level}
                runId={runId}
                status={i < progress.current_level ? 'completed' : i === progress.current_level ? 'in_progress' : 'pending'}
              />
            ))}
          </div>
        </div>

        {/* Status */}
        <div className="mt-6 text-center">
          {run.status === 'completed' && (
            <Link
              to={`/prs/${runId}`}
              className="inline-block bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Review Pull Request →
            </Link>
          )}
          {run.status === 'blocked' && (
            <Link
              to={`/generations/${runId}/halt`}
              className="inline-block bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-medium transition-colors"
            >
              View Halt Report
            </Link>
          )}
        </div>
      </main>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 text-center">
      <div className="text-2xl font-bold text-blue-400">{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  );
}

function LevelRow({ level, currentLevel, runId, status }) {
  return (
    <div className={`flex items-center justify-between p-4 rounded-lg ${
      status === 'completed' ? 'bg-green-900/30 border border-green-700' :
      status === 'in_progress' ? 'bg-blue-900/30 border border-blue-700' :
      'bg-gray-700/50 border border-gray-600'
    }`}>
      <div className="flex items-center gap-4">
        <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
          status === 'completed' ? 'bg-green-600' :
          status === 'in_progress' ? 'bg-blue-600 animate-pulse' :
          'bg-gray-600'
        }`}>
          {level}
        </span>
        <span className="font-medium">Level {level}</span>
      </div>
      <div className="flex items-center gap-4">
        <span className={`text-sm ${
          status === 'completed' ? 'text-green-400' :
          status === 'in_progress' ? 'text-blue-400' :
          'text-gray-400'
        }`}>
          {status === 'completed' ? '✓ Complete' :
           status === 'in_progress' ? '⏳ In Progress' :
           '⏸ Pending'}
        </span>
        {status === 'completed' && (
          <Link
            to={`/generations/${runId}/critic/${level}`}
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            View Critic Log →
          </Link>
        )}
      </div>
    </div>
  );
}

export default GenerationProgress;
