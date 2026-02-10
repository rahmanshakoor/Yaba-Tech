import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2 } from 'lucide-react';
import api from '../../services/api';
import { Button, Input } from '../../components/common';

interface LineItem {
  item_id: string;
  quantity: string;
  unit_cost: string;
}

import { useItems } from '../../hooks/useInventory';

export default function ManualInvoiceForm() {
  const queryClient = useQueryClient();
  const { data: rawItems = [] } = useItems('Raw');
  const [supplier, setSupplier] = useState('');
  const [date, setDate] = useState('');
  const [lines, setLines] = useState<LineItem[]>([
    { item_id: '', quantity: '', unit_cost: '' },
  ]);

  const create = useMutation({
    mutationFn: async () => {
      const items = lines
        .filter((l) => l.item_id && l.quantity && l.unit_cost)
        .map((l) => ({
          item_id: Number(l.item_id),
          quantity: Number(l.quantity),
          unit_cost: Number(l.unit_cost),
        }));
      const totalCost = items.reduce(
        (sum, i) => sum + i.quantity * i.unit_cost,
        0,
      );
      const { data } = await api.post('/invoices/manual', {
        supplier_name: supplier,
        date: date || undefined,
        total_cost: totalCost,
        items,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      setSupplier('');
      setDate('');
      setLines([{ item_id: '', quantity: '', unit_cost: '' }]);
    },
  });

  const addRow = () =>
    setLines([...lines, { item_id: '', quantity: '', unit_cost: '' }]);

  const removeRow = (idx: number) =>
    setLines(lines.filter((_, i) => i !== idx));

  const updateLine = (idx: number, field: keyof LineItem, value: string) => {
    const updated = [...lines];
    updated[idx] = { ...updated[idx], [field]: value };
    setLines(updated);
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        create.mutate();
      }}
      className="space-y-5"
    >
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Supplier"
          value={supplier}
          onChange={(e) => setSupplier(e.target.value)}
          required
        />
        <Input
          label="Date"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">
          Line Items
        </h3>
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600">
                  Item ID
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600">
                  Quantity
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600">
                  Unit Cost
                </th>
                <th className="px-3 py-2 w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {lines.map((line, idx) => (
                <tr key={idx}>
                  <td className="px-3 py-2">
                    <select
                      className="w-full border border-gray-300 rounded px-2 py-1 text-sm bg-white"
                      value={line.item_id}
                      onChange={(e) =>
                        updateLine(idx, 'item_id', e.target.value)
                      }
                    >
                      <option value="">Select Item</option>
                      {rawItems.map((item) => (
                        <option key={item.item_id} value={item.item_id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <input
                      type="number"
                      step="0.1"
                      className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      value={line.quantity}
                      onChange={(e) =>
                        updateLine(idx, 'quantity', e.target.value)
                      }
                      placeholder={
                        line.item_id && rawItems.find(i => i.item_id === Number(line.item_id))
                          ? rawItems.find(i => i.item_id === Number(line.item_id))?.unit
                          : 'Qty'
                      }
                    />
                  </td>
                  <td className="px-3 py-2">
                    <input
                      type="number"
                      step="0.01"
                      className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                      value={line.unit_cost}
                      onChange={(e) =>
                        updateLine(idx, 'unit_cost', e.target.value)
                      }
                      placeholder="Price"
                    />
                  </td>
                  <td className="px-3 py-2">
                    {lines.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeRow(idx)}
                        className="text-red-400 hover:text-red-600"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <button
          type="button"
          onClick={addRow}
          className="mt-2 flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800"
        >
          <Plus size={14} /> Add Row
        </button>
      </div>

      <div className="flex justify-end">
        <Button type="submit" disabled={create.isPending}>
          {create.isPending ? 'Submitting...' : 'Create Invoice'}
        </Button>
      </div>

      {create.isSuccess && (
        <p className="text-sm text-green-600">Invoice created!</p>
      )}
      {create.isError && (
        <p className="text-sm text-red-600">
          Failed to create invoice. Check your data and try again.
        </p>
      )}
    </form>
  );
}
