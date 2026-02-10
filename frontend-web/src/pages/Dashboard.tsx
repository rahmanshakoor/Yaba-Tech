import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  DollarSign,
  FileText,
  Trash2,
} from 'lucide-react';
import api from '../services/api';
import { DataTable } from '../components/common';
import type { DashboardKPIs, ProductionLog } from '../types';

interface KPICardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  color: string;
}

function KPICard({ label, value, icon, color }: KPICardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>{icon}</div>
      </div>
    </div>
  );
}

interface LogRow extends Record<string, unknown> {
  log_id: number;
  output_batch_id: number;
  input_batch_id: number;
  quantity_used: number;
  created_at: string;
}

export default function Dashboard() {
  const { data: kpis } = useQuery<DashboardKPIs>({
    queryKey: ['dashboardKPIs'],
    queryFn: async () => {
      // Aggregate from available endpoints
      const [summaryRes, invoicesRes] = await Promise.all([
        api.get('/inventory/summary'),
        api.get('/invoices/'),
      ]);

      const items = summaryRes.data.items || [];
      const lowStock = items.filter(
        (i: { total_stock: number }) => i.total_stock < 5,
      ).length;

      return {
        lowStockItems: lowStock,
        todaysProductionCost: 0,
        pendingInvoices: (invoicesRes.data || []).length,
        wasteValueWeek: 0,
      };
    },
  });

  const { data: recentLogs = [] } = useQuery<ProductionLog[]>({
    queryKey: ['recentLogs'],
    queryFn: async () => {
      // The backend doesn't have a dedicated recent logs endpoint,
      // so we return an empty array as a placeholder.
      return [];
    },
  });

  const logRows: LogRow[] = recentLogs.slice(0, 5).map((l) => ({
    log_id: l.log_id,
    output_batch_id: l.output_batch_id,
    input_batch_id: l.input_batch_id,
    quantity_used: l.quantity_used,
    created_at: l.created_at,
  }));

  const logColumns = [
    { key: 'log_id', header: 'Log #' },
    { key: 'output_batch_id', header: 'Output Batch' },
    { key: 'input_batch_id', header: 'Input Batch' },
    {
      key: 'quantity_used',
      header: 'Qty Used',
      render: (row: LogRow) => (
        <span className="font-mono">{row.quantity_used}</span>
      ),
    },
    {
      key: 'created_at',
      header: 'Time',
      render: (row: LogRow) =>
        row.created_at
          ? new Date(String(row.created_at)).toLocaleString()
          : '—',
    },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      <div className="grid grid-cols-4 gap-4">
        <KPICard
          label="Low Stock Items"
          value={String(kpis?.lowStockItems ?? '—')}
          icon={<AlertTriangle size={20} className="text-red-600" />}
          color="bg-red-50"
        />
        <KPICard
          label="Today's Production Cost"
          value={`$${(kpis?.todaysProductionCost ?? 0).toFixed(2)}`}
          icon={<DollarSign size={20} className="text-green-600" />}
          color="bg-green-50"
        />
        <KPICard
          label="Pending Invoices"
          value={String(kpis?.pendingInvoices ?? '—')}
          icon={<FileText size={20} className="text-blue-600" />}
          color="bg-blue-50"
        />
        <KPICard
          label="Waste Value (Week)"
          value={`$${(kpis?.wasteValueWeek ?? 0).toFixed(2)}`}
          icon={<Trash2 size={20} className="text-amber-600" />}
          color="bg-amber-50"
        />
      </div>

      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">
          Recent Production Activity
        </h2>
        <DataTable columns={logColumns} data={logRows} keyField="log_id" />
      </div>
    </div>
  );
}
