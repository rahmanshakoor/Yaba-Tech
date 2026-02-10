import { useState } from 'react';
import { Button, Input } from '../../components/common';
import { useItemBatches, useUpdateBatch } from '../../hooks/useInventory';
import type { InventoryBatch } from '../../types';

interface StockAdjustmentProps {
  itemId: number;
  itemName: string;
  onClose: () => void;
}

export default function StockAdjustment({
  itemId,
  itemName,
  onClose,
}: StockAdjustmentProps) {
  const { data: batches = [] } = useItemBatches(itemId);
  const updateBatch = useUpdateBatch();
  const [batchId, setBatchId] = useState<number | ''>('');
  const [newQuantity, setNewQuantity] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (batchId === '' || !newQuantity) return;
    updateBatch.mutate(
      { batchId: Number(batchId), quantity_current: Number(newQuantity) },
      { onSuccess: onClose },
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-sm text-gray-500">
        Adjusting stock for: <strong>{itemName}</strong>
      </p>

      <div className="space-y-1">
        <label htmlFor="adj-batch-select" className="block text-sm font-medium text-gray-700">
          Batch
        </label>
        <select
          id="adj-batch-select"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          value={batchId}
          onChange={(e) => setBatchId(Number(e.target.value))}
          required
        >
          <option value="">Select batch...</option>
          {batches.map((b: InventoryBatch) => (
            <option key={b.batch_id} value={b.batch_id}>
              Batch #{b.batch_id} – Current: {b.quantity_current}
            </option>
          ))}
        </select>
      </div>

      <Input
        label="New Quantity"
        type="number"
        step="0.1"
        min="0"
        value={newQuantity}
        onChange={(e) => setNewQuantity(e.target.value)}
        required
      />

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" type="button" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" disabled={updateBatch.isPending}>
          {updateBatch.isPending ? 'Saving...' : 'Update Stock'}
        </Button>
      </div>
    </form>
  );
}
