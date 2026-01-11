import type { FC } from "react";

const Settings: FC = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
      <p className="text-gray-600">Configure trading parameters and risk management.</p>
      <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-500">
        Configuration options coming soon...
      </div>
    </div>
  );
};

export default Settings;
