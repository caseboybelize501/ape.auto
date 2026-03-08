import React from 'react';
import { useParams } from 'react-router-dom';

function CriticLog() {
  const { runId, level } = useParams();

  // Mock critic log data
  const criticLog = {
    run_id: runId,
    level: parseInt(level),
    files: [
      {
        path: 'src/api/users.py',
        pass1: 'pass',
        pass2: 'pass',
        pass3: 'pass',
        pass4: 'pass',
        repair_count: 0,
      },
      {
        path: 'src/services/auth.py',
        pass1: 'pass',
        pass2: 'fail',
        pass3: 'pass',
        pass4: 'pass',
        repair_count: 1,
      },
    ],
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold">Critic Log - Level {level}</h1>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="bg-gray-800 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">File</th>
                <th className="px-4 py-3 text-center text-sm font-medium">Pass 1<br/><span className="text-gray-400">Syntax</span></th>
                <th className="px-4 py-3 text-center text-sm font-medium">Pass 2<br/><span className="text-gray-400">Contract</span></th>
                <th className="px-4 py-3 text-center text-sm font-medium">Pass 3<br/><span className="text-gray-400">Completeness</span></th>
                <th className="px-4 py-3 text-center text-sm font-medium">Pass 4<br/><span className="text-gray-400">Logic</span></th>
                <th className="px-4 py-3 text-center text-sm font-medium">Repairs</th>
              </tr>
            </thead>
            <tbody>
              {criticLog.files.map((file, i) => (
                <tr key={i} className="border-t border-gray-700">
                  <td className="px-4 py-3 font-mono text-sm">{file.path}</td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge status={file.pass1} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge status={file.pass2} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge status={file.pass3} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge status={file.pass4} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    {file.repair_count > 0 ? (
                      <span className="text-yellow-400">{file.repair_count}</span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div className="mt-6 flex gap-6 text-sm">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-green-600"></span>
            <span>Pass</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-red-600"></span>
            <span>Fail</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-gray-600"></span>
            <span>Skipped</span>
          </div>
        </div>
      </main>
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    pass: 'bg-green-600',
    fail: 'bg-red-600',
    uncertain: 'bg-yellow-600',
    skipped: 'bg-gray-600',
  };

  return (
    <span className={`inline-block w-6 h-6 rounded ${colors[status] || colors.skipped}`} />
  );
}

export default CriticLog;
