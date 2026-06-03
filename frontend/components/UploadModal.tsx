'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { api } from '@/lib/api';
import { Upload, FileText, Loader2, XCircle, CheckCircle } from 'lucide-react';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

export default function UploadModal({ isOpen, onClose, onUploadSuccess }: UploadModalProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  if (!isOpen) return null;

  const handleFile = async (file: File) => {
    if (!file.name.endsWith('.pdf')) {
      setError('Please upload a PDF file');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(false);

    try {
      await api.uploadPDF(file);
      setSuccess(true);
      setTimeout(() => {
        onUploadSuccess();
        onClose();
        setSuccess(false);
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Upload PDF Document</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            disabled={uploading}
          >
            <XCircle className="h-5 w-5" />
          </Button>
        </div>

        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload-modal"
            accept=".pdf"
            onChange={handleChange}
            className="hidden"
            disabled={uploading}
          />

          <label
            htmlFor="file-upload-modal"
            className="cursor-pointer flex flex-col items-center gap-4"
          >
            {uploading ? (
              <>
                <Loader2 className="h-12 w-12 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Processing PDF...</p>
              </>
            ) : success ? (
              <>
                <CheckCircle className="h-12 w-12 text-green-500" />
                <p className="text-sm font-medium text-green-500">PDF indexed successfully!</p>
              </>
            ) : (
              <>
                <Upload className="h-12 w-12 text-muted-foreground" />
                <div>
                  <p className="text-lg font-medium">Upload PDF Document</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Drag and drop or click to browse
                  </p>
                </div>
                <Button type="button" variant="outline">
                  <FileText className="mr-2 h-4 w-4" />
                  Select PDF
                </Button>
              </>
            )}
          </label>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-2 text-destructive">
            <XCircle className="h-4 w-4 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        <div className="mt-4 text-xs text-muted-foreground">
          <p>• Documents are added to your workspace incrementally</p>
          <p>• Chat history is preserved after upload</p>
          <p>• You can upload multiple PDFs</p>
        </div>
      </Card>
    </div>
  );
}
