import type { FC } from "react";

const Dashboard: FC = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
      <p className="text-gray-600">
        Overview of trading activity, positions, and performance metrics.
      </p>
      <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-500">
        Dashboard components coming soon...
      </div>
    </div>
  );
};

export default Dashboard;
