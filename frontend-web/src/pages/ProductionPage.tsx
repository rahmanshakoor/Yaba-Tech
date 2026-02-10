import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useItems } from '../hooks/useInventory';
import ProductionForm from '../features/production/ProductionForm';
import ProductionLogTable from '../features/production/ProductionLogTable';
import type { ProductionLog } from '../types';

export default function ProductionPage() {
  const [tab, setTab] = useState<'record' | 'history'>('record');
  const { data: allItems = [] } = useItems();
  const dishes = allItems.filter((i) => i.type === 'Dish' || i.type === 'Prepped');

  const { data: logs = [] } = useQuery<ProductionLog[]>({
    queryKey: ['productionLogs'],
    queryFn: async () => {
      // Placeholder – the backend doesn't expose a list endpoint yet
      return [];
    },
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Production Station</h1>

      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setTab('record')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'record'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Record
        </button>
        <button
          onClick={() => setTab('history')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'history'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          History
        </button>
      </div>

      {tab === 'record' ? (
        <ProductionForm dishes={dishes} />
      ) : (
        <ProductionLogTable logs={logs} />
      )}
    </div>
  );
}
