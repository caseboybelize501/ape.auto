import React from 'react';
import { Link } from 'react-router-dom';

function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-blue-400">APE</h1>
          <p className="text-gray-400">Autonomous Production Engineer</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <DashboardCard
            title="Submit Requirement"
            description="Start a new requirement implementation"
            link="/requirements/new"
            icon="📝"
          />
          <DashboardCard
            title="Production Dashboard"
            description="Monitor production deployments"
            link="/production"
            icon="📊"
          />
          <DashboardCard
            title="Analytics"
            description="View usage metrics and statistics"
            link="/analytics"
            icon="📈"
          />
        </div>

        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <div className="bg-gray-800 rounded-lg p-6">
            <p className="text-gray-400">No recent activity</p>
          </div>
        </div>
      </main>
    </div>
  );
}

function DashboardCard({ title, description, link, icon }) {
  return (
    <Link to={link} className="block">
      <div className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-colors border border-gray-700 hover:border-blue-500">
        <div className="text-4xl mb-4">{icon}</div>
        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        <p className="text-gray-400">{description}</p>
      </div>
    </Link>
  );
}

export default App;
