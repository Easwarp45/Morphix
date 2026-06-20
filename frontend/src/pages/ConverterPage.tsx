/* =============================================================================
   Converter Page — Advanced Multi-file Drag & Drop, Previews, Batch Operations & WebSockets
   ============================================================================= */

import { useState, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { useQuery } from '@tanstack/react-query';
import {
  Upload, FileText, Image, X,
  Download, CheckCircle2, XCircle, Loader2, Sparkles,
  Link as LinkIcon, Info, HelpCircle, Play
} from 'lucide-react';
import { toast } from 'sonner';
import { fileService, conversionService } from '@/services';
import { useAuth } from '@/stores/auth-context';
import type { ConversionType, FileRecord, Conversion, SupportedFormat } from '@/types';

function TextPreview({ url }: { url: string }) {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetch(url)
      .then(res => res.text())
      .then(text => {
        if (active) {
          setContent(text.slice(0, 500) + (text.length > 500 ? '...' : ''));
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) {
          setContent('Preview unavailable');
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [url]);

  if (loading) return <div className="h-40 flex items-center justify-center text-xs text-[hsl(var(--muted-foreground))]">Loading preview...</div>;

  return (
    <pre className="w-full h-40 rounded-xl border border-[hsl(var(--border))] p-3 text-xs bg-black/5 dark:bg-white/5 overflow-y-auto text-left font-mono whitespace-pre-wrap">
      {content}
    </pre>
  );
}

export function ConverterPage() {
  const { user } = useAuth();
  const [uploadedFiles, setUploadedFiles] = useState<FileRecord[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileRecord | null>(null);
  const [targetFormats, setTargetFormats] = useState<Record<string, string>>({});
  
  // Batch processing state
  const [activeBatchId, setActiveBatchId] = useState<string | null>(null);
  const [batchConversions, setBatchConversions] = useState<Conversion[]>([]);
  const [isProcessingBatch, setIsProcessingBatch] = useState(false);
  const [zipConversion, setZipConversion] = useState<Conversion | null>(null);
  const [shareLinks, setShareLinks] = useState<Record<string, string>>({});

  // Upload state
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [isUploading, setIsUploading] = useState(false);

  // Fetch supported formats
  const { data: formats } = useQuery<SupportedFormat[]>({
    queryKey: ['supported-formats'],
    queryFn: conversionService.getSupportedFormats,
  });

  const maxFileSize = user?.is_guest ? 10 * 1024 * 1024 : 100 * 1024 * 1024;
  const maxFileSizeMB = user?.is_guest ? 10 : 100;

  // File Upload Handlers
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsUploading(true);
    // Initialize file-specific progress
    const progressMap: Record<string, number> = {};
    acceptedFiles.forEach(f => {
      progressMap[f.name] = 0;
    });
    setUploadProgress(progressMap);

    try {
      const result = await fileService.uploadFiles(acceptedFiles, (percent) => {
        // Simple aggregate progress tracking
        setUploadProgress(prev => {
          const updated = { ...prev };
          acceptedFiles.forEach(f => {
            updated[f.name] = percent;
          });
          return updated;
        });
      });

      if (result.uploaded.length > 0) {
        setUploadedFiles(prev => [...prev, ...result.uploaded]);
        // Set first uploaded file as selected
        if (!selectedFile) {
          setSelectedFile(result.uploaded[0]);
        }
        toast.success(`Successfully uploaded ${result.uploaded.length} file(s)`);
      }

      if (result.errors.length > 0) {
        result.errors.forEach(err => {
          toast.error(`${err.file}: ${err.error}`);
        });
      }
    } catch (err: any) {
      toast.error('Upload failed. Check file sizes and quotas.');
    } finally {
      setIsUploading(false);
      setUploadProgress({});
    }
  }, [selectedFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize: maxFileSize,
  });

  // WebSocket / Real-time updates Setup
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token || !activeBatchId) return;

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    const wsHost = API_URL.replace('/api/v1', '').replace('http://', 'ws://').replace('https://', 'wss://');
    const wsUrl = `${wsHost}/ws/conversions/?token=${token}`;

    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === 'conversion_status' && data.conversion) {
          const updated: Conversion = data.conversion;

          // Check if this belongs to our active batch
          if (updated.batch_id === activeBatchId) {
            setBatchConversions(prev => {
              const exists = prev.some(c => c.id === updated.id);
              if (exists) {
                return prev.map(c => c.id === updated.id ? updated : c);
              } else {
                return [...prev, updated];
              }
            });

            // Update local file record statuses
            setUploadedFiles(prev =>
              prev.map(f => {
                if (f.id === updated.source_file) {
                  return {
                    ...f,
                    status: updated.status === 'completed'
                      ? 'completed'
                      : updated.status === 'failed'
                      ? 'failed'
                      : 'processing'
                  };
                }
                return f;
              })
            );
          } else if (zipConversion && updated.id === zipConversion.id) {
            // Check if this is the active ZIP operation status
            setZipConversion(updated);
            if (updated.status === 'completed') {
              toast.success('Batch ZIP archive created!');
              if (updated.download_url) {
                window.open(updated.download_url, '_blank');
              }
            } else if (updated.status === 'failed') {
              toast.error(`ZIP generation failed: ${updated.error_message}`);
            }
          }
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message', err);
      }
    };

    socket.onerror = () => {
      console.warn('WebSocket connection error.');
    };

    // Polling Fallback just in case WebSocket fails/drops
    const fallbackPoll = setInterval(async () => {
      if (socket.readyState !== WebSocket.OPEN) {
        try {
          const status = await conversionService.getBatchStatus(activeBatchId);
          setBatchConversions(status.conversions);
        } catch {
          // ignore
        }
      }
    }, 4000);

    return () => {
      socket.close();
      clearInterval(fallbackPoll);
    };
  }, [activeBatchId, zipConversion?.id]);

  const getAvailableFormats = (file: FileRecord) => {
    if (!formats) return [];
    const match = formats.find(f => f.source_extension === file.file_extension);
    return match?.conversions || [];
  };

  const handleFormatChange = (fileId: string, type: string) => {
    setTargetFormats(prev => ({ ...prev, [fileId]: type }));
  };

  const handleApplyToAll = (type: string) => {
    const formatInfo = formats?.flatMap(f => f.conversions).find(c => c.type === type);
    if (!formatInfo) return;

    const newFormats: Record<string, string> = { ...targetFormats };
    uploadedFiles.forEach(file => {
      const avail = getAvailableFormats(file);
      if (avail.some(c => c.type === type)) {
        newFormats[file.id] = type;
      }
    });
    setTargetFormats(newFormats);
    toast.info(`Applied ${formatInfo.label} to all compatible files.`);
  };

  // Run Batch Conversion
  const handleConvertBatch = async () => {
    const list = uploadedFiles.filter(f => targetFormats[f.id]);
    if (list.length === 0) {
      toast.error('Configure target formats for your files first.');
      return;
    }

    setIsProcessingBatch(true);
    const payload = list.map(f => ({
      source_file_id: f.id,
      conversion_type: targetFormats[f.id] as ConversionType,
      options: {}
    }));

    try {
      const result = await conversionService.createBatchConversion(payload);
      setActiveBatchId(result.batch_id);
      setBatchConversions(result.conversions);
      toast.success('Batch conversion started!');
    } catch {
      toast.error('Failed to start batch conversions.');
      setIsProcessingBatch(false);
    }
  };

  // ZIP batch download
  const handleZipBatch = async () => {
    if (!activeBatchId) return;
    try {
      toast.info('Zipping completed batch files...');
      const zipJob = await conversionService.createBatchZip(activeBatchId);
      setZipConversion(zipJob);
    } catch (err: any) {
      toast.error(err.response?.data?.error?.message || 'Failed to create ZIP download.');
    }
  };

  // Generate share link
  const handleShare = async (conversionId: string) => {
    try {
      const share = await conversionService.createShare(conversionId);
      const host = window.location.origin;
      const fullShareUrl = `${host}${share.share_url}`;
      setShareLinks(prev => ({ ...prev, [conversionId]: fullShareUrl }));
      await navigator.clipboard.writeText(fullShareUrl);
      toast.success('Share link copied to clipboard!');
    } catch {
      toast.error('Failed to create share link.');
    }
  };

  const handleDownloadFile = (url: string | null) => {
    if (!url) return;
    window.open(url, '_blank');
  };

  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== id));
    if (selectedFile?.id === id) {
      setSelectedFile(null);
    }
  };

  const resetBatch = () => {
    setActiveBatchId(null);
    setBatchConversions([]);
    setZipConversion(null);
    setIsProcessingBatch(false);
    setUploadedFiles([]);
    setSelectedFile(null);
    setTargetFormats({});
    setShareLinks({});
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-4xl font-extrabold tracking-tight mb-2">Cloud File Converter</h1>
        <p className="text-[hsl(var(--muted-foreground))]">
          100% Free SaaS. Convert, extract text (OCR), and summarize files securely.
          <span className="ml-1 text-primary-500 font-semibold">
            {user?.is_guest ? 'Guest mode (10MB limit)' : 'Account active (100MB limit)'}
          </span>
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-12 gap-8">
        {/* LEFT COLUMN: Upload, List, and Previews */}
        <div className="lg:col-span-7 space-y-6">
          {/* File Uploader */}
          {!activeBatchId && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="relative"
            >
              <div
                {...getRootProps()}
                className={`p-10 rounded-3xl border-2 border-dashed transition-all cursor-pointer text-center ${
                  isDragActive
                    ? 'border-primary-500 bg-primary-500/5'
                    : 'border-[hsl(var(--border))] hover:border-primary-500/50 bg-[hsl(var(--card))]'
                }`}
                aria-label="File Upload Dropzone"
              >
                <input {...getInputProps()} />
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-500/25">
                  <Upload className={`w-8 h-8 text-white ${isDragActive ? 'animate-bounce' : ''}`} />
                </div>
                {isUploading ? (
                  <div>
                    <p className="font-semibold mb-2">Uploading Files...</p>
                    <div className="w-full max-w-xs mx-auto h-2 rounded-full bg-[hsl(var(--muted))] overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary-500 transition-all duration-300"
                        style={{ width: `${Object.values(uploadProgress)[0] || 0}%` }}
                      />
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="font-semibold text-lg mb-1">
                      {isDragActive ? 'Release to upload!' : 'Drag & drop files here'}
                    </p>
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">
                      or click to upload. Max size: {maxFileSizeMB}MB · Supports PDF, DOCX, TXT, Images, ZIP
                    </p>
                  </>
                )}
              </div>
            </motion.div>
          )}

          {/* Files List */}
          {uploadedFiles.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-6 rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]"
            >
              <h2 className="text-lg font-bold mb-4 flex items-center">
                <FileText className="w-5 h-5 mr-2 text-primary-500" />
                Files Checklist
              </h2>
              <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                {uploadedFiles.map((file) => {
                  const avail = getAvailableFormats(file);
                  const selectedType = targetFormats[file.id] || '';
                  const conversion = batchConversions.find(c => c.source_file === file.id);

                  return (
                    <div
                      key={file.id}
                      onClick={() => setSelectedFile(file)}
                      className={`flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-2xl border transition-all cursor-pointer gap-4 ${
                        selectedFile?.id === file.id
                          ? 'border-primary-500 bg-primary-500/5'
                          : 'border-[hsl(var(--border))] bg-white/5 dark:bg-black/5 hover:border-primary-500/30'
                      }`}
                    >
                      <div className="flex items-center space-x-3 w-full sm:w-auto overflow-hidden">
                        <div className="p-2.5 rounded-xl bg-primary-500/10 flex-shrink-0">
                          {file.is_image ? <Image className="w-5 h-5 text-purple-500" /> : <FileText className="w-5 h-5 text-blue-500" />}
                        </div>
                        <div className="overflow-hidden">
                          <h4 className="font-semibold text-sm truncate max-w-[200px]" title={file.original_name}>{file.original_name}</h4>
                          <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">{file.file_size_mb} MB</p>
                        </div>
                      </div>

                      {/* Format Selector or Conversion Status */}
                      <div className="flex items-center space-x-3 w-full sm:w-auto justify-end">
                        {!activeBatchId ? (
                          <select
                            value={selectedType}
                            onChange={(e) => handleFormatChange(file.id, e.target.value)}
                            onClick={(e) => e.stopPropagation()}
                            className="text-xs px-3 py-2 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--background))] focus:outline-none focus:ring-1 focus:ring-primary-500"
                            aria-label={`Select output format for ${file.original_name}`}
                          >
                            <option value="">Convert To...</option>
                            {avail.map(opt => (
                              <option key={opt.type} value={opt.type}>{opt.label}</option>
                            ))}
                          </select>
                        ) : (
                          /* Render specific progress for this file in active batch */
                          <div className="text-xs flex items-center space-x-2">
                            {conversion?.status === 'completed' && (
                              <div className="flex items-center space-x-1.5">
                                <span className="text-accent-500 font-semibold flex items-center"><CheckCircle2 className="w-4 h-4 mr-1" /> Ready</span>
                                <button
                                  onClick={(e) => { e.stopPropagation(); handleDownloadFile(conversion.download_url); }}
                                  className="p-1.5 bg-accent-500/10 hover:bg-accent-500/20 text-accent-500 rounded-xl transition-all"
                                  title="Download File"
                                >
                                  <Download className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={(e) => { e.stopPropagation(); handleShare(conversion.id); }}
                                  className="p-1.5 bg-primary-500/10 hover:bg-primary-500/20 text-primary-500 rounded-xl transition-all"
                                  title="Copy Share Link"
                                >
                                  <LinkIcon className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            )}
                            {conversion?.status === 'failed' && (
                              <span className="text-red-500 font-medium flex items-center" title={conversion.error_message}>
                                <XCircle className="w-4 h-4 mr-1" /> Failed
                              </span>
                            )}
                            {(conversion?.status === 'pending' || conversion?.status === 'processing') && (
                              <span className="text-primary-500 flex items-center">
                                <Loader2 className="w-4 h-4 mr-1 animate-spin" /> Converting
                              </span>
                            )}
                          </div>
                        )}

                        {!activeBatchId && (
                          <button
                            onClick={(e) => { e.stopPropagation(); removeFile(file.id); }}
                            className="p-2 hover:bg-red-500/10 hover:text-red-500 rounded-xl text-[hsl(var(--muted-foreground))] transition-colors"
                            aria-label={`Remove file ${file.original_name}`}
                          >
                            <X className="w-4.5 h-4.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          )}

          {/* Selected File Preview Box */}
          {selectedFile && (
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-6 rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]"
            >
              <h3 className="text-base font-bold mb-3 flex items-center">
                <Info className="w-4.5 h-4.5 mr-2 text-primary-500" />
                File Preview: {selectedFile.original_name}
              </h3>
              {selectedFile.is_image ? (
                <div className="w-full h-56 rounded-2xl overflow-hidden border border-[hsl(var(--border))] flex items-center justify-center bg-black/5 dark:bg-white/5">
                  <img
                    src={selectedFile.download_url || ''}
                    alt={selectedFile.original_name}
                    className="max-w-full max-h-full object-contain"
                  />
                </div>
              ) : selectedFile.file_extension === 'txt' && selectedFile.download_url ? (
                <TextPreview url={selectedFile.download_url} />
              ) : (
                <div className="w-full h-36 rounded-2xl border border-[hsl(var(--border))] flex flex-col items-center justify-center bg-black/5 dark:bg-white/5 text-[hsl(var(--muted-foreground))]">
                  <FileText className="w-12 h-12 mb-2 opacity-40" />
                  <span className="text-xs font-semibold uppercase">{selectedFile.file_extension} document</span>
                  <p className="text-[10px] text-[hsl(var(--muted-foreground))] mt-1">Preview is not available for this document type</p>
                </div>
              )}
            </motion.div>
          )}
        </div>

        {/* RIGHT COLUMN: Batch Configuration & Active Batch Dashboard */}
        <div className="lg:col-span-5 space-y-6">
          {!activeBatchId ? (
            /* Configure and start Batch */
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-6 rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] space-y-6"
            >
              <h2 className="text-lg font-bold flex items-center">
                <Sparkles className="w-5 h-5 mr-2 text-primary-500" />
                Batch Actions
              </h2>

              {/* Bulk Formats Helper */}
              {uploadedFiles.length > 1 && (
                <div className="p-4 rounded-2xl bg-primary-500/5 border border-primary-500/10 space-y-3">
                  <h4 className="text-xs font-bold text-primary-500 uppercase tracking-wider flex items-center">
                    <Info className="w-3.5 h-3.5 mr-1" /> Multi-file Helper
                  </h4>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">
                    Quickly configure the target conversion format for all compatible files in your checklist:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => handleApplyToAll('png_to_webp')}
                      className="px-2.5 py-1.5 bg-white dark:bg-black border border-[hsl(var(--border))] hover:border-primary-500/50 rounded-lg text-[10px] font-semibold transition-colors"
                    >
                      All Images → WEBP
                    </button>
                    <button
                      onClick={() => handleApplyToAll('pdf_to_txt')}
                      className="px-2.5 py-1.5 bg-white dark:bg-black border border-[hsl(var(--border))] hover:border-primary-500/50 rounded-lg text-[10px] font-semibold transition-colors"
                    >
                      All PDFs → TXT
                    </button>
                    <button
                      onClick={() => handleApplyToAll('ai_summarize')}
                      className="px-2.5 py-1.5 bg-white dark:bg-black border border-[hsl(var(--border))] hover:border-primary-500/50 rounded-lg text-[10px] font-semibold transition-colors"
                    >
                      All Docs → Summarize
                    </button>
                  </div>
                </div>
              )}

              <div className="text-sm text-[hsl(var(--muted-foreground))]">
                {uploadedFiles.length === 0 ? (
                  <div className="text-center py-8">
                    <HelpCircle className="w-12 h-12 mx-auto text-[hsl(var(--muted-foreground))] opacity-20 mb-2" />
                    <p>Ready to convert! Drag and drop files to populate your list.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center text-xs border-b border-[hsl(var(--border))] pb-2">
                      <span>Total files:</span>
                      <span className="font-bold text-[hsl(var(--foreground))]">{uploadedFiles.length}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs border-b border-[hsl(var(--border))] pb-2">
                      <span>Files configured:</span>
                      <span className="font-bold text-[hsl(var(--foreground))]">
                        {uploadedFiles.filter(f => targetFormats[f.id]).length} / {uploadedFiles.length}
                      </span>
                    </div>

                    <button
                      onClick={handleConvertBatch}
                      disabled={isProcessingBatch || uploadedFiles.filter(f => targetFormats[f.id]).length === 0}
                      className="w-full py-3 bg-gradient-to-r from-primary-500 to-purple-600 text-white font-bold rounded-2xl hover:opacity-95 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed shadow-xl shadow-primary-500/25 flex items-center justify-center space-x-2"
                      id="convert-batch-btn"
                    >
                      {isProcessingBatch ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Starting Conversions...</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 fill-current mr-1" />
                          <span>Start Batch Conversion</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          ) : (
            /* Active Batch status board */
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-6 rounded-3xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] space-y-6"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold">Batch Progress</h2>
                <span className="px-2 py-0.5 text-[10px] bg-primary-500/10 text-primary-500 rounded-full font-mono uppercase">
                  {batchConversions.filter(c => c.status === 'completed').length} / {batchConversions.length} Done
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-3 rounded-full bg-[hsl(var(--muted))] overflow-hidden relative">
                <motion.div
                  className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{
                    width: `${
                      batchConversions.length > 0
                        ? (batchConversions.filter(c => c.status === 'completed').length / batchConversions.length) * 100
                        : 0
                    }%`
                  }}
                  transition={{ duration: 0.4 }}
                />
              </div>

              {/* ZIP Download / Options */}
              <div className="space-y-3 pt-2">
                {batchConversions.some(c => c.status === 'completed') && (
                  <button
                    onClick={handleZipBatch}
                    disabled={zipConversion?.status === 'processing' || zipConversion?.status === 'pending'}
                    className="w-full py-3 bg-[hsl(var(--accent))] border border-[hsl(var(--border))] hover:bg-primary-500/10 hover:border-primary-500/30 text-[hsl(var(--foreground))] font-bold rounded-2xl transition-all flex items-center justify-center space-x-2"
                  >
                    {zipConversion?.status === 'processing' || zipConversion?.status === 'pending' ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-primary-500" />
                        <span>Creating ZIP Archive...</span>
                      </>
                    ) : (
                      <>
                        <Download className="w-4 h-4" />
                        <span>Download Completed as ZIP</span>
                      </>
                    )}
                  </button>
                )}

                {/* Reset button to clear batch */}
                <button
                  onClick={resetBatch}
                  className="w-full py-3 border border-red-500/20 hover:bg-red-500/5 text-red-500 font-bold rounded-2xl transition-all"
                >
                  Clear & Start New Batch
                </button>
              </div>

              {/* Copy share links list */}
              {Object.keys(shareLinks).length > 0 && (
                <div className="space-y-2.5 border-t border-[hsl(var(--border))] pt-4">
                  <h4 className="text-xs font-bold text-[hsl(var(--muted-foreground))] uppercase tracking-wider">Shareable Links</h4>
                  {Object.entries(shareLinks).map(([convId, url]) => {
                    const conv = batchConversions.find(c => c.id === convId);
                    return (
                      <div key={convId} className="flex justify-between items-center text-xs p-2 rounded-xl bg-white/5 dark:bg-black/5">
                        <span className="truncate max-w-[150px] font-semibold text-[hsl(var(--muted-foreground))]">{conv?.output_filename}</span>
                        <button
                          onClick={() => { navigator.clipboard.writeText(url); toast.success('Link copied!'); }}
                          className="px-2 py-1 bg-primary-500/15 text-primary-500 rounded-lg text-[10px] font-semibold hover:bg-primary-500/25 transition-all"
                        >
                          Copy Link
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
