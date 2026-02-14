import { useState } from 'react';
import { ChefHat } from 'lucide-react';
import ProduceForm from '../features/production/ProduceForm';
import DepleteForm from '../features/production/DepleteForm';

export default function ProductionPage() {
  const [activeMode, setActiveMode] = useState<'produce' | 'deplete'>('produce');

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <ChefHat size={28} className="text-brand-yellow" />
        <h1 className="text-2xl font-bold text-brand-black">Production Station</h1>
      </div>

      {/* Mode Toggle */}
      <div className="flex rounded-full bg-gray-200 p-1 w-fit">
        <button
          onClick={() => setActiveMode('produce')}
          className={`px-6 py-2 rounded-full text-sm font-semibold transition-colors ${
            activeMode === 'produce'
              ? 'bg-green-600 text-white'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Record Production
        </button>
        <button
          onClick={() => setActiveMode('deplete')}
          className={`px-6 py-2 rounded-full text-sm font-semibold transition-colors ${
            activeMode === 'deplete'
              ? 'bg-blue-600 text-white'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Record Depletion
        </button>
      </div>

      {activeMode === 'produce' ? <ProduceForm /> : <DepleteForm />}
    </div>
  );
}
