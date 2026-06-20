/* =============================================================================
   History Page — Conversion history with search and filters
   ============================================================================= */

import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Search, Download, CheckCircle2, XCircle, Clock, Loader2, FileText, ArrowRightLeft } from 'lucide-react';
import { toast } from 'sonner';
import { analyticsService, conversionService } from '@/services';

interface HistoryItem {
  id: string;
  source_file_name: string;
  conversion_type: string;
  source_format: string;
  target_format: string;
  status: string;
  output_filename: string;
  processing_time: number | null;
  created_at: string;
}

const statusConfig: Record<string, { icon: React.ElementType; color: string; bg: string }> = {
  completed: { icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
  failed: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
  processing: { icon: Loader2, color: 'text-amber-500', bg: 'bg-amber-500/10' },
  pending: { icon: Clock, color: 'text-blue-500', bg: 'bg-blue-500/10' },
};

export function HistoryPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const { data: history = [], isLoading } = useQuery<HistoryItem[]>({
    queryKey: ['conversion-history'],
    queryFn: analyticsService.getHistory as () => Promise<HistoryItem[]>,
  });

  const filtered = history.filter(item => {
    const matchSearch = !search || item.source_file_name.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'all' || item.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const handleDownload = async (id: string) => {
    try {
      const result = await conversionService.downloadConversion(id);
      window.open(result.download_url, '_blank');
    } catch {
      toast.error('Download failed.');
    }
  };

  return (
    <div>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold mb-1">Conversion History</h1>
        <p className="text-[hsl(var(--muted-foreground))] mb-6">View and manage your past conversions</p>
      </motion.div>

      {/* Filters */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[hsl(var(--muted-foreground))]" />
          <input
            type="text"
            placeholder="Search files..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            id="history-search"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors text-sm"
          />
        </div>
        <div className="flex gap-2">
          {['all', 'completed', 'processing', 'failed'].map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${
                statusFilter === status
                  ? 'bg-primary-500/10 text-primary-500 border border-primary-500/30'
                  : 'border border-[hsl(var(--border))] hover:bg-[hsl(var(--accent))]'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </motion.div>

      {/* History List */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-20 rounded-xl shimmer" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-20">
          <FileText className="w-16 h-16 text-[hsl(var(--muted-foreground))] mx-auto mb-4 opacity-30" />
          <p className="font-semibold text-lg mb-1">No conversions found</p>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            {search ? 'Try a different search term' : 'Start converting files to see them here'}
          </p>
        </motion.div>
      ) : (
        <div className="space-y-2">
          {filtered.map((item, i) => {
            const config = statusConfig[item.status] || statusConfig.pending;
            const StatusIcon = config.icon;
            return (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                className="flex items-center justify-between p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] hover:border-primary-500/20 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className={`w-10 h-10 rounded-xl ${config.bg} flex items-center justify-center`}>
                    <StatusIcon className={`w-5 h-5 ${config.color} ${item.status === 'processing' ? 'animate-spin' : ''}`} />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{item.source_file_name}</p>
                    <div className="flex items-center text-xs text-[hsl(var(--muted-foreground))] mt-0.5 space-x-2">
                      <span className="flex items-center"><ArrowRightLeft className="w-3 h-3 mr-1" />{item.conversion_type.replace(/_/g, ' → ')}</span>
                      {item.processing_time && <span>· {item.processing_time.toFixed(1)}s</span>}
                      <span>· {new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                {item.status === 'completed' && (
                  <button onClick={() => handleDownload(item.id)} className="p-2 rounded-lg hover:bg-primary-500/10 text-primary-500 transition-colors" id={`download-${item.id}`}>
                    <Download className="w-5 h-5" />
                  </button>
                )}
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
