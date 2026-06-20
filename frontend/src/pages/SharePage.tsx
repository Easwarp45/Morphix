/* =============================================================================
   Share Page â€” Public unauthenticated download page
   ============================================================================= */

import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Download, FileText, ArrowLeft, Loader2, XCircle } from 'lucide-react';
import { conversionService } from '@/services';
import { toast } from 'sonner';

export function SharePage() {
  const { token } = useParams<{ token: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [shareData, setShareData] = useState<{ download_url: string; filename: string; file_size: number } | null>(null);

  useEffect(() => {
    async function fetchShare() {
      if (!token) return;
      try {
        const data = await conversionService.getPublicShare(token);
        setShareData(data);
      } catch (err: any) {
        const msg = err.response?.data?.error?.message || 'This share link is invalid or has expired.';
        setError(msg);
      } finally {
        setLoading(false);
      }
    }
    fetchShare();
  }, [token]);

  const handleDownload = () => {
    if (!shareData) return;
    window.open(shareData.download_url, '_blank');
    toast.success('Download started!');
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center gradient-bg pt-16">
      {/* Background orbs */}
      <div className="gradient-orb w-96 h-96 bg-primary-500/20 -top-20 -left-20" />
      <div className="gradient-orb w-80 h-80 bg-purple-500/15 bottom-20 right-10" />

      <div className="relative z-10 w-full max-w-md mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-8 rounded-3xl glass border border-[hsl(var(--border))]"
        >
          <div className="text-center mb-6">
            <Link to="/" className="inline-flex items-center text-xs text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] mb-4 transition-colors">
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Home
            </Link>
            <h1 className="text-2xl font-bold tracking-tight">Shared File Download</h1>
            <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">This link is temporary and secure</p>
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-10">
              <Loader2 className="w-10 h-10 text-primary-500 animate-spin mb-4" />
              <p className="text-sm text-[hsl(var(--muted-foreground))]">Retrieving download link...</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-6 text-center">
              <XCircle className="w-12 h-12 text-red-500 mb-4" />
              <h3 className="font-semibold text-lg mb-1">Link Unavailable</h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))] mb-6">{error}</p>
              <Link to="/" className="px-6 py-2.5 rounded-xl font-semibold bg-gradient-to-r from-primary-500 to-purple-600 text-white hover:opacity-90 transition-opacity">
                Go to morphixert
              </Link>
            </div>
          ) : shareData ? (
            <div>
              <div className="p-4 rounded-2xl border border-[hsl(var(--border))] bg-white/5 flex items-center space-x-4 mb-6">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div className="overflow-hidden">
                  <h3 className="font-semibold text-sm truncate" title={shareData.filename}>{shareData.filename}</h3>
                  <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">{formatSize(shareData.file_size)}</p>
                </div>
              </div>

              <button
                onClick={handleDownload}
                className="w-full py-3 rounded-xl font-semibold bg-gradient-to-r from-primary-500 to-purple-600 text-white hover:opacity-90 transition-opacity shadow-lg shadow-primary-500/25 flex items-center justify-center"
              >
                <Download className="w-5 h-5 mr-2" /> Download File
              </button>
            </div>
          ) : null}
        </motion.div>
      </div>
    </div>
  );
}
