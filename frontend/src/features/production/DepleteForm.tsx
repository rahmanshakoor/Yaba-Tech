import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle } from 'lucide-react';
import api from '../../services/api';
import { useItems, useInventorySummary } from '../../hooks/useInventory';
import { Button } from '../../components/common';
import type { Item } from '../../types';

export default function DepleteForm() {
  const queryClient = useQueryClient();
  const { data: allItems = [] } = useItems();
  const { data: summaryData } = useInventorySummary();
  const summaryItems = summaryData?.items ?? [];

  const [selectedItem, setSelectedItem] = useState<number | ''>('');
  const [quantity, setQuantity] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const getStockForItem = (itemId: number): number => {
    const found = summaryItems.find((s) => s.item_id === itemId);
    return found ? found.total_stock : 0;
  };

  const currentStock = selectedItem !== '' ? getStockForItem(selectedItem) : 0;
  const enteredQty = Number(quantity) || 0;
  const isInsufficientStock = selectedItem !== '' && enteredQty > 0 && enteredQty > currentStock;

  const deplete = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/inventory/deplete', {
        item_id: Number(selectedItem),
        quantity: Number(quantity),
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventorySummary'] });
      queryClient.invalidateQueries({ queryKey: ['allBatches'] });
      queryClient.invalidateQueries({ queryKey: ['batches'] });
      setSelectedItem('');
      setQuantity('');
      setValidationError(null);
    },
  });

  const handleSubmit = () => {
    if (selectedItem === '') {
      setValidationError('Please select an item.');
      return;
    }
    if (!quantity || Number(quantity) <= 0) {
      setValidationError('Please enter a valid quantity.');
      return;
    }
    if (isInsufficientStock) {
      return;
    }
    setValidationError(null);
    deplete.mutate();
  };

  return (
    <div className="bg-brand-black text-brand-white rounded-xl p-8 space-y-6">
      <h2 className="text-xl font-bold text-blue-400">Deplete Stock</h2>

      {/* Select Item */}
      <div className="space-y-1">
        <label htmlFor="deplete-item" className="block text-sm font-medium text-gray-300">
          Select Item
        </label>
        <select
          id="deplete-item"
          className="block w-full rounded-md bg-gray-800 border border-gray-600 text-white px-4 py-3 text-base"
          value={selectedItem}
          onChange={(e) => {
            setSelectedItem(e.target.value === '' ? '' : Number(e.target.value));
            setValidationError(null);
          }}
        >
          <option value="">Choose an item to deplete...</option>
          {allItems.map((d: Item) => (
            <option key={d.item_id} value={d.item_id}>
              {d.name} ({d.type})
            </option>
          ))}
        </select>
      </div>

      {/* Stock Info */}
      {selectedItem !== '' && (
        <p className="text-sm text-gray-400">
          Current stock: <span className="font-semibold text-white">{currentStock}</span>
        </p>
      )}

      {/* Quantity */}
      <div className="space-y-1">
        <label htmlFor="deplete-qty" className="block text-sm font-medium text-gray-300">
          Quantity
        </label>
        <input
          id="deplete-qty"
          type="number"
          step="1"
          min="1"
          className="block w-full rounded-md bg-gray-800 border border-gray-600 text-white px-4 py-3 text-lg"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          placeholder="How many sold / used?"
        />
      </div>

      {/* Validation Error */}
      {validationError && (
        <div className="flex items-center gap-2 bg-red-900/50 border border-red-700 text-red-300 rounded-md px-4 py-3 text-sm" role="alert">
          <AlertTriangle size={16} />
          {validationError}
        </div>
      )}

      {/* Insufficient Stock Error */}
      {isInsufficientStock && (
        <p className="text-sm text-red-500 font-medium">Insufficient stock available.</p>
      )}

      {/* Submit */}
      <div className="pt-2">
        <Button
          onClick={handleSubmit}
          disabled={deplete.isPending || isInsufficientStock}
          className="bg-brand-yellow text-brand-charcoal hover:bg-yellow-400 border-0"
        >
          {deplete.isPending ? 'Logging...' : 'Log Depletion'}
        </Button>
      </div>

      {deplete.isSuccess && (
        <p className="text-sm text-green-400">Depletion logged successfully!</p>
      )}
      {deplete.isError && (
        <p className="text-sm text-red-400">
          Error: {(deplete.error as any).response?.data?.detail || deplete.error.message}
        </p>
      )}
    </div>
  );
}
