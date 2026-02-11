import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import api from '../services/api';
import { useItems } from '../hooks/useInventory';
import { useDebounce } from '../hooks/useDebounce';
import { Modal, Button, Input, DataTable } from '../components/common';
import RecipeList from '../features/recipes/RecipeList';
import RecipeBuilder from '../features/recipes/RecipeBuilder';
import type { Item, ItemType } from '../types';

interface SelectedIngredient {
  input_item_id: number;
  name: string;
  unit: string;
  quantity: number;
}

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
  ingredients: SelectedIngredient[];
}

const emptyForm: ItemFormData = {
  name: '',
  unit: '',
  type: 'Raw',
  shelf_life_days: '7',
  ingredients: [],
};

export default function DefinitionsPage() {
  const [tab, setTab] = useState<'items' | 'recipes'>('items');
  const { data: allItems = [], isLoading } = useItems();
  const queryClient = useQueryClient();

  // Ingredient search state
  const [ingSearch, setIngSearch] = useState('');
  const debouncedIngSearch = useDebounce(ingSearch);
  const [addQuantity, setAddQuantity] = useState<Record<number, string>>({});

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
    mutationFn: async (payload: { name: string; unit: string; type: ItemType; shelf_life_days: number; ingredients: SelectedIngredient[] }) => {
      // 1. Create the item
      const { data: item } = await api.post('/items/', {
        name: payload.name,
        unit: payload.unit,
        type: payload.type,
        shelf_life_days: payload.shelf_life_days,
      });

      // 2. If there are ingredients, save the composition
      if (payload.ingredients && payload.ingredients.length > 0) {
        const compositionPayload = payload.ingredients.map((ing) => ({
          input_item_id: ing.input_item_id,
          quantity: ing.quantity,
        }));
        await api.post(`/items/${item.item_id}/composition`, compositionPayload);
      }

      return item;
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
    setIngSearch('');
    setAddQuantity({});
    setShowItemModal(true);
  };

  const openEditModal = (item: Item) => {
    setEditingItem(item);
    setForm({
      name: item.name,
      unit: item.unit,
      type: item.type,
      shelf_life_days: String(item.shelf_life_days),
      ingredients: [], // Editing ingredients not supported in this modal yet
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
      ingredients: form.ingredients,
    };
    if (editingItem) {
      // Exclude ingredients from update payload
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { ingredients, ...updatePayload } = payload;
      updateItem.mutate({ id: editingItem.item_id, ...updatePayload });
    } else {
      createItem.mutate(payload);
    }
  };

  const handleAddIngredient = (item: Item) => {
    const qty = Number(addQuantity[item.item_id] || 1);
    if (qty <= 0) return;

    if (form.ingredients.some((ing) => ing.input_item_id === item.item_id)) return;

    setForm({
      ...form,
      ingredients: [
        ...form.ingredients,
        { input_item_id: item.item_id, name: item.name, unit: item.unit, quantity: qty },
      ],
    });
    setAddQuantity((prev) => ({ ...prev, [item.item_id]: '' }));
  };

  const handleRemoveIngredient = (id: number) => {
    setForm({
      ...form,
      ingredients: form.ingredients.filter((i) => i.input_item_id !== id),
    });
  };

  // Filter available items for ingredients
  const availableIngredients = allItems.filter((item) => {
    if (!item.name.toLowerCase().includes(debouncedIngSearch.toLowerCase())) return false;

    // Prevent selecting the item itself is unnecessary since it's a new item (no ID yet)
    // But we should follow type rules
    if (form.type === 'Prepped') {
      return item.type === 'Raw';
    }
    if (form.type === 'Dish') {
      return item.type === 'Raw' || item.type === 'Prepped';
    }
    return false;
  });

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
      <h1 className="text-2xl font-bold text-brand-black">Definitions</h1>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setTab('items')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === 'items'
            ? 'border-brand-yellow text-brand-black'
            : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
        >
          Items
        </button>
        <button
          onClick={() => setTab('recipes')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === 'recipes'
            ? 'border-brand-yellow text-brand-black'
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

          {/* Ingredient Selector for New Prepped/Dish Items */}
          {!editingItem && (form.type === 'Prepped' || form.type === 'Dish') && (
            <div className="space-y-2 border-t pt-4 mt-2">
              <h3 className="text-sm font-medium text-gray-700">Ingredients</h3>

              {/* Selected Ingredients List */}
              {form.ingredients.length > 0 && (
                <div className="border border-indigo-100 rounded-md bg-indigo-50 divide-y divide-indigo-100 mb-2">
                  {form.ingredients.map((ing) => (
                    <div key={ing.input_item_id} className="flex justify-between items-center p-2 text-sm">
                      <span>{ing.name} <span className="text-gray-500">({ing.quantity} {ing.unit})</span></span>
                      <button
                        type="button"
                        onClick={() => handleRemoveIngredient(ing.input_item_id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Search and Add */}
              <Input
                placeholder="Search ingredients..."
                value={ingSearch}
                onChange={(e) => setIngSearch(e.target.value)}
                className="mb-2"
              />
              <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-md divide-y divide-gray-100">
                {availableIngredients.map((item) => (
                  <div key={item.item_id} className="flex items-center gap-2 p-2 text-sm hover:bg-gray-50">
                    <span className="flex-1">{item.name} <span className="text-gray-400">({item.unit})</span></span>
                    <input
                      type="number"
                      className="w-16 border rounded px-1 py-0.5 text-xs"
                      placeholder="Qty"
                      min="0.1"
                      step="0.1"
                      value={addQuantity[item.item_id] ?? ''}
                      onChange={(e) => setAddQuantity({ ...addQuantity, [item.item_id]: e.target.value })}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddIngredient(item);
                        }
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => handleAddIngredient(item)}
                      className="text-indigo-600 hover:bg-indigo-50 p-1 rounded"
                    >
                      <Plus size={16} />
                    </button>
                  </div>
                ))}
                {availableIngredients.length === 0 && (
                  <p className="text-xs text-center text-gray-400 py-2">No matching ingredients</p>
                )}
              </div>
            </div>
          )}

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
