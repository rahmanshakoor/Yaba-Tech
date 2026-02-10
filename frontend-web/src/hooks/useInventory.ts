import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import type {
  Item,
  InventorySummaryItem,
  InventoryBatch,
  WasteReason,
  WasteLog,
} from '../types';

export function useItems(type?: string) {
  return useQuery<Item[]>({
    queryKey: ['items', type],
    queryFn: async () => {
      const params = type ? { type } : {};
      const { data } = await api.get('/items/', { params });
      return data;
    },
  });
}

export function useInventorySummary() {
  return useQuery<{ items: InventorySummaryItem[]; total_inventory_value: number }>({
    queryKey: ['inventorySummary'],
    queryFn: async () => {
      const { data } = await api.get('/inventory/summary');
      return data;
    },
  });
}

export function useItemBatches(itemId: number | null) {
  return useQuery<InventoryBatch[]>({
    queryKey: ['batches', itemId],
    queryFn: async () => {
      const { data } = await api.get(`/inventory/batches/${itemId}`);
      return data;
    },
    enabled: itemId !== null,
  });
}

export function useLogWaste() {
  const queryClient = useQueryClient();
  return useMutation<
    WasteLog,
    Error,
    { batch_id: number; quantity: number; reason: WasteReason }
  >({
    mutationFn: async (payload) => {
      const { data } = await api.post('/inventory/waste', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventorySummary'] });
      queryClient.invalidateQueries({ queryKey: ['batches'] });
    },
  });
}

export function useUpdateBatch() {
  const queryClient = useQueryClient();
  return useMutation<
    InventoryBatch,
    Error,
    { batchId: number; quantity_current: number }
  >({
    mutationFn: async ({ batchId, quantity_current }) => {
      const { data } = await api.put(`/inventory/batch/${batchId}`, {
        quantity_current,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventorySummary'] });
      queryClient.invalidateQueries({ queryKey: ['batches'] });
    },
  });
}
