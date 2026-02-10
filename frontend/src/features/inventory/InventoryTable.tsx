import { DataTable, StatusBadge, Button } from '../../components/common';
import type { Item, InventorySummaryItem } from '../../types';

interface InventoryRow extends Record<string, unknown> {
  item_id: number;
  name: string;
  type: string;
  currentStock: number;
  unit: string;
  shelf_life_days: number;
  status: string;
}

interface InventoryTableProps {
  items: Item[];
  stockData: InventorySummaryItem[];
  onLogWaste: (item: Item) => void;
  onEdit: (item: Item) => void;
}

function getStockStatus(stock: number): string {
  if (stock <= 0) return 'Low';
  if (stock < 5) return 'Low Stock';
  return 'In Stock';
}

export default function InventoryTable({
  items,
  stockData,
  onLogWaste,
  onEdit,
}: InventoryTableProps) {
  const stockMap = new Map(
    stockData.map((s) => [s.item_id, s.total_stock]),
  );

  const rows: InventoryRow[] = items.map((item) => {
    const stock = stockMap.get(item.item_id) ?? 0;
    return {
      item_id: item.item_id,
      name: item.name,
      type: item.type,
      currentStock: stock,
      unit: item.unit,
      shelf_life_days: item.shelf_life_days,
      status: getStockStatus(stock),
    };
  });

  const columns = [
    { key: 'name', header: 'Name' },
    { key: 'type', header: 'Type' },
    {
      key: 'currentStock',
      header: 'Current Stock',
      render: (row: InventoryRow) => (
        <span className="font-mono">{row.currentStock.toFixed(1)}</span>
      ),
    },
    { key: 'unit', header: 'Unit' },
    {
      key: 'shelf_life_days',
      header: 'Shelf Life',
      render: (row: InventoryRow) => <span>{row.shelf_life_days}d</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row: InventoryRow) => <StatusBadge status={row.status} />,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: InventoryRow) => {
        const item = items.find((i) => i.item_id === row.item_id);
        if (!item) return null;
        return (
          <div className="flex gap-2">
            <Button variant="danger" onClick={() => onLogWaste(item)}>
              Log Waste
            </Button>
            <Button variant="secondary" onClick={() => onEdit(item)}>
              Edit
            </Button>
          </div>
        );
      },
    },
  ];

  return <DataTable columns={columns} data={rows} keyField="item_id" />;
}
