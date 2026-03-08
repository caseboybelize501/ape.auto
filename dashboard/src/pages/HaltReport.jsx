import React from 'react';
import { useParams } from 'react-router-dom';

function HaltReport() {
  const { runId } = useParams();

  // Mock halt report
  const haltReport = {
    id: `halt-${runId}`,
    level: 2,
    file_path: 'src/services/payment.py',
    failing_passes: ['contract', 'logic'],
    attempts: [
      {
        attempt_number: 1,
        changes_made: 'Fixed function signature',
        success: false,
      },
      {
        attempt_number: 2,
        changes_made: 'Updated return type',
        success: false,
      },
      {
        attempt_number: 3,
        changes_made: 'Added error handling',
        success: false,
      },
    ],
    recommended_action: 'The contract signature may need to be revised. The implementation logic conflicts with the specified interface.',
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-red-400">GATE-4: Halt Report</h1>
          <p className="text-gray-400">Generation blocked - human intervention required</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Alert */}
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-2">Generation Halted</h2>
          <p className="text-gray-300">
            The critic was unable to validate the generated code after 3 repair attempts.
            Please review and take action.
          </p>
        </div>

        {/* Details */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h3 className="font-semibold mb-4">Halt Details</h3>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-gray-400">File</dt>
              <dd className="font-mono">{haltReport.file_path}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-400">Level</dt>
              <dd>{haltReport.level}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-400">Failing Passes</dt>
              <dd className="flex gap-2">
                {haltReport.failing_passes.map((pass, i) => (
                  <span key={i} className="px-2 py-1 bg-red-900 text-red-400 rounded text-sm">
                    {pass}
                  </span>
                ))}
              </dd>
            </div>
          </dl>
        </div>

        {/* Attempts */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h3 className="font-semibold mb-4">Repair Attempts</h3>
          <div className="space-y-3">
            {haltReport.attempts.map((attempt, i) => (
              <div key={i} className="flex items-center gap-4 p-3 bg-gray-900 rounded">
                <span className="text-sm text-gray-400">Attempt {attempt.attempt_number}</span>
                <span className="text-sm">{attempt.changes_made}</span>
                <span className={`text-sm ${attempt.success ? 'text-green-400' : 'text-red-400'}`}>
                  {attempt.success ? '✓' : '✗'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendation */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h3 className="font-semibold mb-4">Recommended Action</h3>
          <p className="text-gray-300">{haltReport.recommended_action}</p>
        </div>

        {/* Actions */}
        <div className="space-y-4">
          <h3 className="font-semibold">Choose Action</h3>
          <div className="grid grid-cols-2 gap-4">
            <ActionButton
              label="Modify Architecture"
              description="Update the architecture plan and restart generation"
              variant="blue"
            />
            <ActionButton
              label="Modify Requirement"
              description="Clarify the requirement and restart"
              variant="blue"
            />
            <ActionButton
              label="Manual Fix"
              description="I'll fix this file manually, then continue"
              variant="green"
            />
            <ActionButton
              label="Skip File"
              description="Skip this file and continue with remaining files"
              variant="yellow"
            />
          </div>
        </div>
      </main>
    </div>
  );
}

function ActionButton({ label, description, variant }) {
  const variants = {
    blue: 'bg-blue-600 hover:bg-blue-700',
    green: 'bg-green-600 hover:bg-green-700',
    yellow: 'bg-yellow-600 hover:bg-yellow-700',
  };

  return (
    <button className={`${variants[variant]} p-4 rounded-lg text-left transition-colors`}>
      <div className="font-medium">{label}</div>
      <div className="text-sm text-gray-300">{description}</div>
    </button>
  );
}

export default HaltReport;
