import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Undo2 } from 'lucide-react';
import api from '../../services/api';
import { DataTable, Button } from '../../components/common';
import type { ProductionLog } from '../../types';

interface ProductionLogRow extends Record<string, unknown> {
  log_id: number;
  output_batch_id: number;
  input_batch_id: number;
  quantity_used: number;
  created_at: string;
}

interface ProductionLogTableProps {
  logs: ProductionLog[];
}

export default function ProductionLogTable({ logs }: ProductionLogTableProps) {
  const queryClient = useQueryClient();

  const revert = useMutation({
    mutationFn: async (logId: number) => {
      await api.post(`/production/${logId}/revert`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productionLogs'] });
      queryClient.invalidateQueries({ queryKey: ['inventorySummary'] });
    },
  });

  const rows: ProductionLogRow[] = logs.map((l) => ({
    log_id: l.log_id,
    output_batch_id: l.output_batch_id,
    input_batch_id: l.input_batch_id,
    quantity_used: l.quantity_used,
    created_at: l.created_at,
  }));

  const columns = [
    { key: 'log_id', header: 'Log #' },
    { key: 'output_batch_id', header: 'Output Batch' },
    { key: 'input_batch_id', header: 'Input Batch' },
    {
      key: 'quantity_used',
      header: 'Qty Used',
      render: (row: ProductionLogRow) => (
        <span className="font-mono">{row.quantity_used}</span>
      ),
    },
    {
      key: 'created_at',
      header: 'Time',
      render: (row: ProductionLogRow) =>
        new Date(String(row.created_at)).toLocaleTimeString(),
    },
    {
      key: 'actions',
      header: '',
      render: (row: ProductionLogRow) => (
        <Button
          variant="secondary"
          onClick={() => revert.mutate(row.log_id)}
          disabled={revert.isPending}
        >
          <Undo2 size={14} className="inline mr-1" />
          Revert
        </Button>
      ),
    },
  ];

  return <DataTable columns={columns} data={rows} keyField="log_id" />;
}
