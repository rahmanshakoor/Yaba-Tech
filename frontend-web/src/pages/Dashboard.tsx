import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  DollarSign,
  FileText,
  Trash2,
} from 'lucide-react';
import api from '../services/api';
import { DataTable } from '../components/common';

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

interface DashboardStats {
  lowStockItems: number;
  todaysProductionCost: number;
  pendingInvoices: number;
  wasteValueWeek: number;
}

interface DashboardLog extends Record<string, unknown> {
  log_id: number;
  output_batch_id: number;
  input_batch_id: number;
  quantity_used: number;
  created_at: string;
  output_item_name: string;
  input_item_name: string;
}

export default function Dashboard() {
  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ['dashboardStats'],
    queryFn: async () => {
      const response = await api.get('/dashboard/stats');
      return response.data;
    },
  });

  const { data: recentLogs = [] } = useQuery<DashboardLog[]>({
    queryKey: ['recentLogs'],
    queryFn: async () => {
      const response = await api.get('/dashboard/recent-logs');
      return response.data;
    },
  });

  const logColumns = [
    { key: 'log_id', header: 'Log #' },
    { key: 'output_item_name', header: 'Output Item' },
    { key: 'input_item_name', header: 'Input Item' },
    {
      key: 'quantity_used',
      header: 'Qty Used',
      render: (row: DashboardLog) => (
        <span className="font-mono">{row.quantity_used}</span>
      ),
    },
    {
      key: 'created_at',
      header: 'Time',
      render: (row: DashboardLog) =>
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
          value={String(stats?.lowStockItems ?? '—')}
          icon={<AlertTriangle size={20} className="text-red-600" />}
          color="bg-red-50"
        />
        <KPICard
          label="Today's Production Cost"
          value={`$${(stats?.todaysProductionCost ?? 0).toFixed(2)}`}
          icon={<DollarSign size={20} className="text-green-600" />}
          color="bg-green-50"
        />
        <KPICard
          label="Pending Invoices"
          value={String(stats?.pendingInvoices ?? '—')}
          icon={<FileText size={20} className="text-blue-600" />}
          color="bg-blue-50"
        />
        <KPICard
          label="Waste Value (Week)"
          value={`$${(stats?.wasteValueWeek ?? 0).toFixed(2)}`}
          icon={<Trash2 size={20} className="text-amber-600" />}
          color="bg-amber-50"
        />
      </div>

      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">
          Recent Production Activity
        </h2>
        <DataTable columns={logColumns} data={recentLogs} keyField="log_id" />
      </div>
    </div>
  );
}
