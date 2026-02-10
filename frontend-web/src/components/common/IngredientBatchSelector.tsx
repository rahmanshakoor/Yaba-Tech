import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertCircle, Check } from 'lucide-react';
import api from '../../services/api';
import type { InventoryBatch } from '../../types';

interface IngredientBatchSelectorProps {
    ingredientName: string;
    itemId: number;
    quantityNeeded: number;
    onSelect: (batchId: number | null) => void;
    selectedBatchId: number | null;
}

export default function IngredientBatchSelector({
    ingredientName,
    itemId,
    quantityNeeded,
    onSelect,
    selectedBatchId,
}: IngredientBatchSelectorProps) {
    const { data: batches = [], isLoading, error } = useQuery<InventoryBatch[]>({
        queryKey: ['batches', itemId],
        queryFn: async () => {
            const { data } = await api.get(`/inventory/batches/${itemId}`);
            return data;
        },
    });

    // Automatically select the first valid batch if none selected? 
    // No, strict manual mode means explicit selection or nothing (if we want to force it).
    // But maybe better DX to default to FIFO or let user pick.
    // Implementation plan said "Strict" manual mode. So user must pick.

    const selectedBatch = batches.find(b => b.batch_id === selectedBatchId);
    const sufficientInfo = selectedBatch ? (selectedBatch.quantity_current >= quantityNeeded) : false;

    if (isLoading) return <div className="text-gray-400 text-sm animate-pulse">Loading batches...</div>;
    if (error) return <div className="text-red-400 text-sm">Failed to load batches</div>;

    return (
        <div className="bg-gray-800/50 rounded-md p-3 border border-gray-700 space-y-2">
            <div className="flex justify-between items-center">
                <span className="text-gray-300 font-medium">{ingredientName}</span>
                <span className="text-xs text-gray-500">Need: {quantityNeeded}</span>
            </div>

            <select
                className={`w-full bg-gray-900 border ${selectedBatchId && !sufficientInfo ? 'border-red-500 focus:border-red-500' : 'border-gray-600 focus:border-amber-500'
                    } rounded px-3 py-2 text-sm text-white`}
                value={selectedBatchId || ''}
                onChange={(e) => onSelect(e.target.value ? Number(e.target.value) : null)}
            >
                <option value="">-- Select a Batch --</option>
                {batches.map((batch) => (
                    <option
                        key={batch.batch_id}
                        value={batch.batch_id}
                        disabled={batch.quantity_current < quantityNeeded}
                        className={batch.quantity_current < quantityNeeded ? 'text-gray-500 bg-gray-900' : ''}
                    >
                        #{batch.batch_id} - Qty: {batch.quantity_current}
                        {batch.expiration_date ? ` (Exp: ${new Date(batch.expiration_date).toLocaleDateString()})` : ''}
                    </option>
                ))}
            </select>

            {selectedBatchId && (
                <div className="text-xs">
                    {!sufficientInfo ? (
                        <span className="text-red-400 flex items-center gap-1">
                            <AlertCircle size={12} /> Insufficient quantity in selected batch!
                        </span>
                    ) : (
                        <span className="text-green-400 flex items-center gap-1">
                            <Check size={12} /> Batch selected
                        </span>
                    )}
                </div>
            )}

            {batches.length === 0 && (
                <div className="text-red-400 text-xs flex items-center gap-1">
                    <AlertCircle size={12} /> No active batches found
                </div>
            )}
        </div>
    );
}
