import type { FC } from "react";

const Orders: FC = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Orders</h2>
      <p className="text-gray-600">View and manage trading orders.</p>
      <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-500">
        Order history and management coming soon...
      </div>
    </div>
  );
};

export default Orders;
