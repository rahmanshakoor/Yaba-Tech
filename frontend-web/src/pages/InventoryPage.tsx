import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { Modal, Button, Input, DataTable } from '../components/common';
import { useItems, useInventorySummary, useLogWaste, useUpdateBatch } from '../hooks/useInventory';
import type { Item, WasteReason, InventoryBatch } from '../types';

interface BatchRow extends Record<string, unknown> {
  batch_id: number;
  item_name: string;
  item_type: string;
  quantity_initial: number;
  quantity_current: number;
  unit_cost: number;
  total_value: number;
  expiration_date: string | null;
  item_id: number;
}

type FilterType = 'All' | 'Raw' | 'Prepped';

export default function InventoryPage() {
  const { data: allItems = [], isLoading: itemsLoading } = useItems();
  const { data: summaryData } = useInventorySummary();
  const [filter, setFilter] = useState<FilterType>('All');

  // Fetch all batches
  const { data: allBatches = [], isLoading: batchesLoading } = useQuery<InventoryBatch[]>({
    queryKey: ['allBatches'],
    queryFn: async () => {
      const { data } = await api.get('/inventory/batches');
      return data;
    },
  });

  // Modal states
  const [editBatch, setEditBatch] = useState<BatchRow | null>(null);
  const [wasteBatch, setWasteBatch] = useState<BatchRow | null>(null);
  const [newQuantity, setNewQuantity] = useState('');
  const [wasteReason, setWasteReason] = useState<WasteReason>('Spoiled');

  const updateBatch = useUpdateBatch();
  const logWaste = useLogWaste();

  const itemMap = useMemo(() => {
    const map = new Map<number, Item>();
    allItems.forEach((item) => map.set(item.item_id, item));
    return map;
  }, [allItems]);

  const costMap = useMemo(() => {
    const map = new Map<number, number>();
    if (summaryData?.items) {
      summaryData.items.forEach((s) => map.set(s.item_id, s.unit_cost));
    }
    return map;
  }, [summaryData]);

  const rows: BatchRow[] = useMemo(() => {
    return allBatches.map((b) => {
      const item = itemMap.get(b.item_id);
      const unitCost = costMap.get(b.item_id) ?? 0;
      return {
        batch_id: b.batch_id,
        item_name: item?.name ?? `Item #${b.item_id}`,
        item_type: item?.type ?? 'Raw',
        quantity_initial: b.quantity_initial,
        quantity_current: b.quantity_current,
        unit_cost: unitCost,
        total_value: b.quantity_current * unitCost,
        expiration_date: b.expiration_date,
        item_id: b.item_id,
      };
    });
  }, [allBatches, itemMap, costMap]);

  const filteredRows = useMemo(() => {
    if (filter === 'All') return rows;
    return rows.filter((r) => r.item_type === filter);
  }, [rows, filter]);

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editBatch || !newQuantity) return;
    updateBatch.mutate(
      { batchId: editBatch.batch_id, quantity_current: Number(newQuantity) },
      {
        onSuccess: () => {
          setEditBatch(null);
          setNewQuantity('');
        },
      },
    );
  };

  const handleWasteSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!wasteBatch) return;
    logWaste.mutate(
      { batch_id: wasteBatch.batch_id, quantity: wasteBatch.quantity_current, reason: wasteReason },
      {
        onSuccess: () => {
          setWasteBatch(null);
          setWasteReason('Spoiled');
        },
      },
    );
  };

  const columns = [
    { key: 'batch_id', header: 'Batch ID' },
    { key: 'item_name', header: 'Item Name' },
    {
      key: 'quantity_initial',
      header: 'Original Qty',
      render: (row: BatchRow) => <span className="font-mono">{row.quantity_initial}</span>,
    },
    {
      key: 'quantity_current',
      header: 'Current Qty',
      render: (row: BatchRow) => <span className="font-mono">{row.quantity_current}</span>,
    },
    {
      key: 'unit_cost',
      header: 'Unit Cost',
      render: (row: BatchRow) => (
        <span className="font-mono">${row.unit_cost.toFixed(2)}</span>
      ),
    },
    {
      key: 'total_value',
      header: 'Total Value',
      render: (row: BatchRow) => (
        <span className="font-mono">${row.total_value.toFixed(2)}</span>
      ),
    },
    {
      key: 'expiration_date',
      header: 'Expiration Date',
      render: (row: BatchRow) => (
        <span>{row.expiration_date ? new Date(String(row.expiration_date)).toLocaleDateString() : '—'}</span>
      ),
    },
    { key: 'item_type', header: 'Type' },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: BatchRow) => (
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => {
              setEditBatch(row);
              setNewQuantity(String(row.quantity_current));
            }}
          >
            Edit Batch
          </Button>
          <Button variant="danger" onClick={() => setWasteBatch(row)}>
            Log Waste
          </Button>
        </div>
      ),
    },
  ];

  if (itemsLoading || batchesLoading) {
    return <p className="text-gray-400 py-8 text-center">Loading inventory…</p>;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>

      {/* Filter Buttons */}
      <div className="flex gap-2">
        {(['All', 'Raw', 'Prepped'] as FilterType[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${filter === f
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
          >
            {f}
          </button>
        ))}
      </div>

      <DataTable columns={columns} data={filteredRows} keyField="batch_id" />

      {/* Total Inventory Value */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-700">Total Inventory Value</span>
        <span className="text-lg font-bold text-indigo-600">
          ${(summaryData?.total_inventory_value ?? 0).toFixed(2)}
        </span>
      </div>

      {/* Edit Batch Modal */}
      <Modal
        isOpen={!!editBatch}
        onClose={() => setEditBatch(null)}
        title="Edit Batch"
      >
        {editBatch && (
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <p className="text-sm text-gray-500">
              Adjusting Batch #{editBatch.batch_id} — <strong>{editBatch.item_name}</strong>
            </p>
            <Input
              label="Current Quantity"
              type="number"
              step="0.1"
              min="0"
              value={newQuantity}
              onChange={(e) => setNewQuantity(e.target.value)}
              required
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => setEditBatch(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={updateBatch.isPending}>
                {updateBatch.isPending ? 'Saving...' : 'Update Batch'}
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Log Waste Modal */}
      <Modal
        isOpen={!!wasteBatch}
        onClose={() => setWasteBatch(null)}
        title="Log Waste"
      >
        {wasteBatch && (
          <form onSubmit={handleWasteSubmit} className="space-y-4">
            <p className="text-sm text-gray-500">
              Logging waste for Batch #{wasteBatch.batch_id} — <strong>{wasteBatch.item_name}</strong>
            </p>
            <p className="text-sm text-gray-500">
              Current quantity ({wasteBatch.quantity_current}) will be set to 0.
            </p>
            <div className="space-y-1">
              <label htmlFor="waste-reason" className="block text-sm font-medium text-gray-700">
                Reason
              </label>
              <select
                id="waste-reason"
                className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={wasteReason}
                onChange={(e) => setWasteReason(e.target.value as WasteReason)}
              >
                <option value="Spoiled">Spoiled</option>
                <option value="Dropped">Dropped</option>
                <option value="Burned">Burned</option>
                <option value="Theft">Theft</option>
              </select>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => setWasteBatch(null)}>
                Cancel
              </Button>
              <Button variant="danger" type="submit" disabled={logWaste.isPending}>
                {logWaste.isPending ? 'Logging...' : 'Log Waste'}
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
