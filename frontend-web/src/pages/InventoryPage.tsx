import { useState } from 'react';
import { Modal } from '../components/common';
import { useItems, useInventorySummary } from '../hooks/useInventory';
import InventoryTable from '../features/inventory/InventoryTable';
import WasteModal from '../features/inventory/WasteModal';
import StockAdjustment from '../features/inventory/StockAdjustment';
import type { Item } from '../types';

export default function InventoryPage() {
  const { data: items = [], isLoading } = useItems();
  const { data: summaryData } = useInventorySummary();
  const stockData = summaryData?.items ?? [];

  const [wasteItem, setWasteItem] = useState<Item | null>(null);
  const [editItem, setEditItem] = useState<Item | null>(null);

  if (isLoading) {
    return <p className="text-gray-400 py-8 text-center">Loading inventory…</p>;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>

      <InventoryTable
        items={items}
        stockData={stockData}
        onLogWaste={setWasteItem}
        onEdit={setEditItem}
      />

      {/* Waste Modal */}
      <Modal
        isOpen={!!wasteItem}
        onClose={() => setWasteItem(null)}
        title="Log Waste"
      >
        {wasteItem && (
          <WasteModal
            itemId={wasteItem.item_id}
            itemName={wasteItem.name}
            onClose={() => setWasteItem(null)}
          />
        )}
      </Modal>

      {/* Edit / Stock Adjustment Modal */}
      <Modal
        isOpen={!!editItem}
        onClose={() => setEditItem(null)}
        title="Adjust Stock"
      >
        {editItem && (
          <StockAdjustment
            itemId={editItem.item_id}
            itemName={editItem.name}
            onClose={() => setEditItem(null)}
          />
        )}
      </Modal>
    </div>
  );
}
