import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { Button, Input } from '../../components/common';
import type { Item, ProductionResponse } from '../../types';

interface ProductionFormProps {
  dishes: Item[];
}

export default function ProductionForm({ dishes }: ProductionFormProps) {
  const queryClient = useQueryClient();
  const [selectedDish, setSelectedDish] = useState<number | ''>('');
  const [quantity, setQuantity] = useState('');
  const [stockMessage, setStockMessage] = useState<string | null>(null);

  const checkStock = useMutation({
    mutationFn: async () => {
      const { data } = await api.get(
        `/items/${selectedDish}/recipe`,
      );
      return data;
    },
    onSuccess: (data) => {
      if (data.ingredients?.length > 0) {
        setStockMessage('Stock check passed – ingredients available.');
      } else {
        setStockMessage('No recipe defined for this dish.');
      }
    },
    onError: () => setStockMessage('Could not verify stock.'),
  });

  const recordProduction = useMutation<ProductionResponse, Error>({
    mutationFn: async () => {
      const { data } = await api.post('/production/record', {
        output_item_id: Number(selectedDish),
        quantity_to_produce: Number(quantity),
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productionLogs'] });
      queryClient.invalidateQueries({ queryKey: ['inventorySummary'] });
      setSelectedDish('');
      setQuantity('');
      setStockMessage(null);
    },
  });

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-5">
      <h2 className="text-lg font-semibold text-gray-800">Record Production</h2>

      <div className="space-y-1">
        <label htmlFor="dish-select" className="block text-sm font-medium text-gray-700">
          Select Dish
        </label>
        <select
          id="dish-select"
          className="block w-full rounded-md border border-gray-300 px-3 py-3 text-base"
          value={selectedDish}
          onChange={(e) => {
            setSelectedDish(Number(e.target.value));
            setStockMessage(null);
          }}
        >
          <option value="">Choose a dish...</option>
          {dishes.map((d) => (
            <option key={d.item_id} value={d.item_id}>
              {d.name}
            </option>
          ))}
        </select>
      </div>

      <Input
        label="Quantity"
        type="number"
        step="1"
        min="1"
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        className="text-lg py-3"
      />

      {stockMessage && (
        <p className="text-sm px-3 py-2 rounded bg-blue-50 text-blue-700">
          {stockMessage}
        </p>
      )}

      <div className="flex gap-3">
        <Button
          variant="secondary"
          onClick={() => checkStock.mutate()}
          disabled={!selectedDish || checkStock.isPending}
        >
          {checkStock.isPending ? 'Checking...' : 'Check Stock'}
        </Button>
        <Button
          onClick={() => recordProduction.mutate()}
          disabled={
            !selectedDish || !quantity || recordProduction.isPending
          }
        >
          {recordProduction.isPending
            ? 'Recording...'
            : 'Record Production'}
        </Button>
      </div>

      {recordProduction.isError && (
        <p className="text-sm text-red-600">
          Error: {recordProduction.error.message}
        </p>
      )}
    </div>
  );
}
