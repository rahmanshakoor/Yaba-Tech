import { useState } from 'react';
import InvoiceUploader from '../features/invoices/InvoiceUploader';
import ManualInvoiceForm from '../features/invoices/ManualInvoiceForm';

export default function InvoicesPage() {
  const [tab, setTab] = useState<'upload' | 'manual'>('upload');

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>

      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setTab('upload')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'upload'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Upload
        </button>
        <button
          onClick={() => setTab('manual')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'manual'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Manual Entry
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        {tab === 'upload' ? <InvoiceUploader /> : <ManualInvoiceForm />}
      </div>
    </div>
  );
}
