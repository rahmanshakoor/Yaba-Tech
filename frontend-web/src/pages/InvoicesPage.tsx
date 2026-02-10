import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, FileText } from 'lucide-react';
import api from '../services/api';
import { Modal, Button } from '../components/common';
import InvoiceUploader from '../features/invoices/InvoiceUploader';
import ManualInvoiceForm from '../features/invoices/ManualInvoiceForm';
import type { Invoice } from '../types';

export default function InvoicesPage() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [addMode, setAddMode] = useState<'choose' | 'ocr' | 'manual'>('choose');
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  const { data: invoices = [] } = useQuery<Invoice[]>({
    queryKey: ['invoices'],
    queryFn: async () => {
      const { data } = await api.get('/invoices/');
      return data;
    },
  });

  const openAddModal = () => {
    setAddMode('choose');
    setShowAddModal(true);
  };

  const closeAddModal = () => {
    setShowAddModal(false);
    setAddMode('choose');
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
        <Button onClick={openAddModal}>
          <Plus size={16} className="inline mr-1" />
          Add Invoice
        </Button>
      </div>

      {/* Split View */}
      <div className="grid grid-cols-3 gap-6">
        {/* Left: Invoice List */}
        <div className="col-span-1 bg-white border border-gray-200 rounded-lg p-4 max-h-[70vh] overflow-y-auto">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">All Invoices</h2>
          {invoices.length === 0 ? (
            <p className="text-sm text-gray-400 py-4 text-center">No invoices yet</p>
          ) : (
            <div className="space-y-1">
              {invoices.map((inv) => (
                <button
                  key={inv.invoice_id}
                  onClick={() => setSelectedInvoice(inv)}
                  className={`w-full text-left px-4 py-3 rounded-md text-sm font-medium transition-colors ${
                    selectedInvoice?.invoice_id === inv.invoice_id
                      ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <span className="block font-medium">{inv.supplier_name}</span>
                  <span className="text-xs text-gray-400">
                    ${inv.total_cost.toFixed(2)} · {inv.invoice_date ? new Date(inv.invoice_date).toLocaleDateString() : 'No date'}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Invoice Details */}
        <div className="col-span-2 bg-white border border-gray-200 rounded-lg p-6">
          {selectedInvoice ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <FileText size={24} className="text-indigo-600" />
                <h2 className="text-lg font-semibold text-gray-800">
                  Invoice #{selectedInvoice.invoice_id}
                </h2>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Supplier</span>
                  <p className="font-medium">{selectedInvoice.supplier_name}</p>
                </div>
                <div>
                  <span className="text-gray-500">Total Cost</span>
                  <p className="font-medium">${selectedInvoice.total_cost.toFixed(2)}</p>
                </div>
                <div>
                  <span className="text-gray-500">Invoice Date</span>
                  <p className="font-medium">
                    {selectedInvoice.invoice_date
                      ? new Date(selectedInvoice.invoice_date).toLocaleDateString()
                      : '—'}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Created</span>
                  <p className="font-medium">
                    {selectedInvoice.created_at
                      ? new Date(selectedInvoice.created_at).toLocaleString()
                      : '—'}
                  </p>
                </div>
              </div>
              {selectedInvoice.image_url && (
                <div>
                  <span className="text-sm text-gray-500">Attached Image</span>
                  <img
                    src={selectedInvoice.image_url}
                    alt="Invoice"
                    className="mt-2 rounded-lg border border-gray-200 max-h-64 object-contain"
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
              Select an invoice to view details
            </div>
          )}
        </div>
      </div>

      {/* Add Invoice Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={closeAddModal}
        title="Add Invoice"
      >
        {addMode === 'choose' && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">How would you like to add this invoice?</p>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setAddMode('ocr')}
                className="border border-gray-200 rounded-lg p-6 text-center hover:bg-gray-50 transition-colors"
              >
                <span className="block text-lg font-semibold text-gray-800">Auto OCR</span>
                <span className="text-sm text-gray-500 mt-1 block">Upload an image</span>
              </button>
              <button
                onClick={() => setAddMode('manual')}
                className="border border-gray-200 rounded-lg p-6 text-center hover:bg-gray-50 transition-colors"
              >
                <span className="block text-lg font-semibold text-gray-800">Manually</span>
                <span className="text-sm text-gray-500 mt-1 block">Enter details step by step</span>
              </button>
            </div>
          </div>
        )}
        {addMode === 'ocr' && (
          <div className="space-y-4">
            <Button variant="secondary" onClick={() => setAddMode('choose')}>
              ← Back
            </Button>
            <InvoiceUploader />
          </div>
        )}
        {addMode === 'manual' && (
          <div className="space-y-4">
            <Button variant="secondary" onClick={() => setAddMode('choose')}>
              ← Back
            </Button>
            <ManualInvoiceForm />
          </div>
        )}
      </Modal>
    </div>
  );
}
