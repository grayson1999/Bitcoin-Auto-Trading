import type { FC } from "react";

const Signals: FC = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Trading Signals</h2>
      <p className="text-gray-600">
        AI-generated trading signals with confidence scores.
      </p>
      <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-500">
        Signal history and analysis coming soon...
      </div>
    </div>
  );
};

export default Signals;
