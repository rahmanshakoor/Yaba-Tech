import { useState } from 'react';
import { Button, Input } from '../../components/common';
import type { InventoryBatch, WasteReason } from '../../types';
import { useItemBatches, useLogWaste } from '../../hooks/useInventory';

interface WasteModalProps {
  itemId: number;
  itemName: string;
  onClose: () => void;
}

const reasons: WasteReason[] = ['Spoiled', 'Dropped', 'Burned', 'Theft'];

export default function WasteModal({ itemId, itemName, onClose }: WasteModalProps) {
  const { data: batches = [] } = useItemBatches(itemId);
  const logWaste = useLogWaste();
  const [batchId, setBatchId] = useState<number | ''>('');
  const [quantity, setQuantity] = useState('');
  const [reason, setReason] = useState<WasteReason>('Spoiled');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (batchId === '' || !quantity) return;
    logWaste.mutate(
      { batch_id: Number(batchId), quantity: Number(quantity), reason },
      { onSuccess: onClose },
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-sm text-gray-500">Logging waste for: <strong>{itemName}</strong></p>

      <div className="space-y-1">
        <label htmlFor="batch-select" className="block text-sm font-medium text-gray-700">Batch</label>
        <select
          id="batch-select"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          value={batchId}
          onChange={(e) => setBatchId(Number(e.target.value))}
          required
        >
          <option value="">Select batch...</option>
          {batches.map((b: InventoryBatch) => (
            <option key={b.batch_id} value={b.batch_id}>
              Batch #{b.batch_id} – Qty: {b.quantity_current}
            </option>
          ))}
        </select>
      </div>

      <Input
        label="Quantity"
        type="number"
        step="0.1"
        min="0"
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        required
      />

      <div className="space-y-1">
        <label htmlFor="reason-select" className="block text-sm font-medium text-gray-700">Reason</label>
        <select
          id="reason-select"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          value={reason}
          onChange={(e) => setReason(e.target.value as WasteReason)}
        >
          {reasons.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" type="button" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="danger" type="submit" disabled={logWaste.isPending}>
          {logWaste.isPending ? 'Logging...' : 'Log Waste'}
        </Button>
      </div>
    </form>
  );
}
