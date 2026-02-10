import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, ChefHat, CheckCircle } from 'lucide-react';
import api from '../services/api';
import { useItems } from '../hooks/useInventory';
import { Button } from '../components/common';
import type { Item, Recipe, ProductionResponse } from '../types';

export default function ProductionPage() {
  const queryClient = useQueryClient();
  const { data: allItems = [] } = useItems();
  const producible = allItems.filter((i) => i.type === 'Dish' || i.type === 'Prepped');

  const [selectedItem, setSelectedItem] = useState<number | ''>('');
  const [quantity, setQuantity] = useState('');
  const [stockMessage, setStockMessage] = useState<string | null>(null);
  const [stockOk, setStockOk] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [manualBatches, setManualBatches] = useState(false);

  // Fetch recipe for selected item
  const { data: recipe } = useQuery<Recipe>({
    queryKey: ['recipe', selectedItem],
    queryFn: async () => {
      const { data } = await api.get(`/items/${selectedItem}/recipe`);
      return data;
    },
    enabled: selectedItem !== '',
  });

  const checkStock = useMutation({
    mutationFn: async () => {
      const { data } = await api.get(`/items/${selectedItem}/recipe`);
      return data as Recipe;
    },
    onSuccess: (data) => {
      if (data.ingredients?.length > 0) {
        setStockMessage('Stock check passed – ingredients available.');
        setStockOk(true);
      } else {
        setStockMessage('No recipe defined for this item.');
        setStockOk(false);
      }
    },
    onError: () => {
      setStockMessage('Could not verify stock.');
      setStockOk(false);
    },
  });

  const recordProduction = useMutation<ProductionResponse, Error>({
    mutationFn: async () => {
      const { data } = await api.post('/production/record', {
        output_item_id: Number(selectedItem),
        quantity_to_produce: Number(quantity),
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productionLogs'] });
      queryClient.invalidateQueries({ queryKey: ['inventorySummary'] });
      queryClient.invalidateQueries({ queryKey: ['allBatches'] });
      setSelectedItem('');
      setQuantity('');
      setStockMessage(null);
      setStockOk(false);
      setValidationError(null);
    },
  });

  const handleSubmit = () => {
    if (selectedItem === '') {
      setValidationError('Please select an item to produce.');
      return;
    }
    if (!quantity || Number(quantity) <= 0) {
      setValidationError('Please enter a valid quantity.');
      return;
    }
    setValidationError(null);
    recordProduction.mutate();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <ChefHat size={28} className="text-amber-500" />
        <h1 className="text-2xl font-bold text-gray-900">Production Station</h1>
      </div>

      {/* Chef Mode Form */}
      <div className="bg-gray-900 text-white rounded-xl p-8 space-y-6">
        <h2 className="text-xl font-bold text-amber-400">Chef Mode</h2>

        {/* Select Item */}
        <div className="space-y-1">
          <label htmlFor="production-item" className="block text-sm font-medium text-gray-300">
            Select Item
          </label>
          <select
            id="production-item"
            className="block w-full rounded-md bg-gray-800 border border-gray-600 text-white px-4 py-3 text-base"
            value={selectedItem}
            onChange={(e) => {
              setSelectedItem(e.target.value === '' ? '' : Number(e.target.value));
              setStockMessage(null);
              setStockOk(false);
              setValidationError(null);
            }}
          >
            <option value="">Choose a dish or prepped component...</option>
            {producible.map((d: Item) => (
              <option key={d.item_id} value={d.item_id}>
                {d.name} ({d.type})
              </option>
            ))}
          </select>
        </div>

        {/* Quantity */}
        <div className="space-y-1">
          <label htmlFor="production-qty" className="block text-sm font-medium text-gray-300">
            Quantity to Produce
          </label>
          <input
            id="production-qty"
            type="number"
            step="1"
            min="1"
            className="block w-full rounded-md bg-gray-800 border border-gray-600 text-white px-4 py-3 text-lg"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="How many to make?"
          />
        </div>

        {/* Validation Error */}
        {validationError && (
          <div className="flex items-center gap-2 bg-red-900/50 border border-red-700 text-red-300 rounded-md px-4 py-3 text-sm" role="alert">
            <AlertTriangle size={16} />
            {validationError}
          </div>
        )}

        {/* Stock Message */}
        {stockMessage && (
          <div
            className={`flex items-center gap-2 rounded-md px-4 py-3 text-sm ${
              stockOk
                ? 'bg-green-900/50 border border-green-700 text-green-300'
                : 'bg-yellow-900/50 border border-yellow-700 text-yellow-300'
            }`}
          >
            {stockOk ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
            {stockMessage}
          </div>
        )}

        {/* Manual Batch Selection Toggle */}
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
            <input
              type="checkbox"
              checked={manualBatches}
              onChange={(e) => setManualBatches(e.target.checked)}
              className="rounded border-gray-600 bg-gray-800"
            />
            Choose batches manually (override FIFO)
          </label>
        </div>

        {/* Recipe Ingredients Preview */}
        {manualBatches && selectedItem !== '' && recipe?.ingredients && recipe.ingredients.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-4 space-y-2">
            <h3 className="text-sm font-semibold text-gray-300">Ingredients to be used (FIFO default)</h3>
            <div className="divide-y divide-gray-700">
              {recipe.ingredients.map((ing) => (
                <div key={ing.composition_id} className="flex justify-between py-2 text-sm">
                  <span className="text-gray-300">{ing.input_item_name}</span>
                  <span className="text-gray-400 font-mono">
                    {ing.quantity_required} × {quantity || 1}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4 pt-2">
          <Button
            variant="secondary"
            onClick={() => {
              if (selectedItem === '') {
                setValidationError('Please select an item first.');
                return;
              }
              setValidationError(null);
              checkStock.mutate();
            }}
            disabled={checkStock.isPending}
            className="bg-gray-700 border-gray-600 text-white hover:bg-gray-600"
          >
            {checkStock.isPending ? 'Checking...' : 'Check Stock'}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={recordProduction.isPending}
            className="bg-amber-500 text-gray-900 hover:bg-amber-400 border-0"
          >
            {recordProduction.isPending ? 'Producing...' : 'Produce'}
          </Button>
        </div>

        {recordProduction.isSuccess && (
          <p className="text-sm text-green-400">Production recorded successfully!</p>
        )}
        {recordProduction.isError && (
          <p className="text-sm text-red-400">
            Error: {recordProduction.error.message}
          </p>
        )}
      </div>
    </div>
  );
}
