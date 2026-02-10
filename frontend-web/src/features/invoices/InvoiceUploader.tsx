import { useCallback, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Upload } from 'lucide-react';
import api from '../../services/api';
import { Button } from '../../components/common';

export default function InvoiceUploader() {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  const upload = useMutation({
    mutationFn: async (f: File) => {
      const formData = new FormData();
      formData.append('file', f);
      const { data } = await api.post('/invoices/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    },
    onSuccess: () => setFile(null),
  });

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }, []);

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-10 text-center transition-colors ${
          dragActive
            ? 'border-indigo-400 bg-indigo-50'
            : 'border-gray-300 bg-gray-50'
        }`}
      >
        <Upload size={32} className="mx-auto text-gray-400 mb-3" />
        <p className="text-sm text-gray-500">
          Drag &amp; drop an invoice image here, or{' '}
          <label className="text-indigo-600 cursor-pointer hover:underline">
            browse
            <input
              type="file"
              className="hidden"
              accept="image/*"
              onChange={(e) => {
                if (e.target.files?.[0]) setFile(e.target.files[0]);
              }}
            />
          </label>
        </p>
      </div>

      {file && (
        <div className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3">
          <span className="text-sm text-gray-700">{file.name}</span>
          <Button
            onClick={() => upload.mutate(file)}
            disabled={upload.isPending}
          >
            {upload.isPending ? 'Uploading...' : 'Upload & Process'}
          </Button>
        </div>
      )}

      {upload.isSuccess && (
        <p className="text-sm text-green-600">Invoice processed successfully!</p>
      )}
      {upload.isError && (
        <p className="text-sm text-red-600">Upload failed. Please try again.</p>
      )}
    </div>
  );
}
