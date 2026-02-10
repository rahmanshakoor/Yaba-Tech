import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import api from '../services/api';
import { useItems } from '../hooks/useInventory';
import { Modal, Button, Input, DataTable } from '../components/common';
import RecipeList from '../features/recipes/RecipeList';
import RecipeBuilder from '../features/recipes/RecipeBuilder';
import type { Item, ItemType } from '../types';

interface ItemRow extends Record<string, unknown> {
  item_id: number;
  name: string;
  unit: string;
  type: string;
  shelf_life_days: number;
}

interface ItemFormData {
  name: string;
  unit: string;
  type: ItemType;
  shelf_life_days: string;
}

const emptyForm: ItemFormData = {
  name: '',
  unit: '',
  type: 'Raw',
  shelf_life_days: '7',
};

export default function DefinitionsPage() {
  const [tab, setTab] = useState<'items' | 'recipes'>('items');
  const { data: allItems = [], isLoading } = useItems();
  const queryClient = useQueryClient();

  // Item modal state
  const [showItemModal, setShowItemModal] = useState(false);
  const [editingItem, setEditingItem] = useState<Item | null>(null);
  const [form, setForm] = useState<ItemFormData>(emptyForm);

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState<Item | null>(null);

  // Recipe state
  const dishes = allItems.filter((i) => i.type === 'Dish' || i.type === 'Prepped');
  const [selectedDish, setSelectedDish] = useState<Item | null>(null);

  const createItem = useMutation({
    mutationFn: async (payload: { name: string; unit: string; type: ItemType; shelf_life_days: number }) => {
      const { data } = await api.post('/items/', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items'] });
      closeItemModal();
    },
  });

  const updateItem = useMutation({
    mutationFn: async ({ id, ...payload }: { id: number; name: string; unit: string; type: ItemType; shelf_life_days: number }) => {
      const { data } = await api.put(`/items/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items'] });
      closeItemModal();
    },
  });

  const deleteItem = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/items/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items'] });
      setDeleteTarget(null);
    },
  });

  const openAddModal = () => {
    setEditingItem(null);
    setForm(emptyForm);
    setShowItemModal(true);
  };

  const openEditModal = (item: Item) => {
    setEditingItem(item);
    setForm({
      name: item.name,
      unit: item.unit,
      type: item.type,
      shelf_life_days: String(item.shelf_life_days),
    });
    setShowItemModal(true);
  };

  const closeItemModal = () => {
    setShowItemModal(false);
    setEditingItem(null);
    setForm(emptyForm);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      name: form.name,
      unit: form.unit,
      type: form.type,
      shelf_life_days: Number(form.shelf_life_days),
    };
    if (editingItem) {
      updateItem.mutate({ id: editingItem.item_id, ...payload });
    } else {
      createItem.mutate(payload);
    }
  };

  const rows: ItemRow[] = allItems.map((item) => ({
    item_id: item.item_id,
    name: item.name,
    unit: item.unit,
    type: item.type,
    shelf_life_days: item.shelf_life_days,
  }));

  const columns = [
    { key: 'name', header: 'Name' },
    { key: 'unit', header: 'Unit' },
    { key: 'type', header: 'Type' },
    {
      key: 'shelf_life_days',
      header: 'Shelf Life',
      render: (row: ItemRow) => <span>{row.shelf_life_days}d</span>,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: ItemRow) => {
        const item = allItems.find((i) => i.item_id === row.item_id);
        if (!item) return null;
        return (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => openEditModal(item)}>
              <Pencil size={14} className="inline mr-1" />
              Edit
            </Button>
            <Button variant="danger" onClick={() => setDeleteTarget(item)}>
              <Trash2 size={14} className="inline mr-1" />
              Delete
            </Button>
          </div>
        );
      },
    },
  ];

  if (isLoading) {
    return <p className="text-gray-400 py-8 text-center">Loading definitions…</p>;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Definitions</h1>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setTab('items')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'items'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Items
        </button>
        <button
          onClick={() => setTab('recipes')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'recipes'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Recipes
        </button>
      </div>

      {/* Tab Content */}
      {tab === 'items' ? (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={openAddModal}>
              <Plus size={16} className="inline mr-1" />
              Add Item Type
            </Button>
          </div>
          <DataTable columns={columns} data={rows} keyField="item_id" />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-1 bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-gray-700">Dishes / Prepped</h2>
              </div>
              <RecipeList
                dishes={dishes}
                selectedId={selectedDish?.item_id ?? null}
                onSelect={setSelectedDish}
              />
            </div>
            <div className="col-span-2">
              {selectedDish ? (
                <RecipeBuilder dish={selectedDish} allItems={allItems} targetItemType={selectedDish.type} />
              ) : (
                <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
                  Select a dish to view or edit its recipe
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Item Modal */}
      <Modal
        isOpen={showItemModal}
        onClose={closeItemModal}
        title={editingItem ? 'Edit Item Type' : 'Add Item Type'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <Input
            label="Unit"
            value={form.unit}
            onChange={(e) => setForm({ ...form, unit: e.target.value })}
            placeholder="e.g. kg, liters, pieces"
            required
          />
          <div className="space-y-1">
            <label htmlFor="item-type-select" className="block text-sm font-medium text-gray-700">
              Type
            </label>
            <select
              id="item-type-select"
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value as ItemType })}
            >
              <option value="Raw">Raw</option>
              <option value="Prepped">Prepped</option>
              <option value="Dish">Dish</option>
            </select>
          </div>
          <Input
            label="Shelf Life (days)"
            type="number"
            min="1"
            value={form.shelf_life_days}
            onChange={(e) => setForm({ ...form, shelf_life_days: e.target.value })}
            required
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={closeItemModal}>
              Cancel
            </Button>
            <Button type="submit" disabled={createItem.isPending || updateItem.isPending}>
              {createItem.isPending || updateItem.isPending ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Item Type"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Are you sure you want to delete <strong>{deleteTarget?.name}</strong>? This action cannot be undone.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => deleteTarget && deleteItem.mutate(deleteTarget.item_id)}
              disabled={deleteItem.isPending}
            >
              {deleteItem.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
