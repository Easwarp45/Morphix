/* =============================================================================
   Dashboard Page — Stats, charts, and recent activity
   ============================================================================= */

import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { FileText, ArrowRightLeft, Download, HardDrive, TrendingUp } from 'lucide-react';
import { analyticsService } from '@/services';
import type { DashboardStats } from '@/types';

export function DashboardPage() {
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: analyticsService.getDashboardStats,
  });

  if (isLoading || !stats) {
    return <DashboardSkeleton />;
  }

  const statCards = [
    { label: 'Total Files', value: stats.total_files, icon: FileText, color: 'from-blue-500 to-cyan-500', bg: 'bg-blue-500/10' },
    { label: 'Conversions', value: stats.completed_conversions, icon: ArrowRightLeft, color: 'from-primary-500 to-purple-500', bg: 'bg-primary-500/10' },
    { label: 'Downloads', value: stats.total_downloads, icon: Download, color: 'from-emerald-500 to-teal-500', bg: 'bg-emerald-500/10' },
    { label: 'Storage Used', value: `${stats.storage.used_mb} MB`, icon: HardDrive, color: 'from-amber-500 to-orange-500', bg: 'bg-amber-500/10' },
  ];

  return (
    <div>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold mb-1">Dashboard</h1>
        <p className="text-[hsl(var(--muted-foreground))] mb-8">Welcome back! Here&apos;s your overview.</p>
      </motion.div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-5 rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] hover:border-primary-500/30 transition-colors"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                <card.icon className="w-5 h-5 text-white" />
              </div>
              <TrendingUp className="w-4 h-4 text-accent-500" />
            </div>
            <div className="text-2xl font-bold">{card.value}</div>
            <div className="text-sm text-[hsl(var(--muted-foreground))]">{card.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Storage Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="p-6 rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] mb-8"
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold flex items-center">
            <HardDrive className="w-5 h-5 mr-2 text-primary-500" />
            Storage Usage
          </h3>
          <span className="text-sm text-[hsl(var(--muted-foreground))]">
            {stats.storage.used_mb} / {stats.storage.limit_mb} MB
          </span>
        </div>
        <div className="w-full h-3 rounded-full bg-[hsl(var(--muted))] overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(stats.storage.percent, 100)}%` }}
            transition={{ duration: 1, delay: 0.5 }}
            className={`h-full rounded-full ${
              stats.storage.percent > 80
                ? 'bg-gradient-to-r from-red-500 to-orange-500'
                : 'bg-gradient-to-r from-primary-500 to-purple-500'
            }`}
          />
        </div>
        <p className="text-xs text-[hsl(var(--muted-foreground))] mt-2">
          {stats.storage.percent}% used
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Conversion Activity Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="p-6 rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]"
        >
          <h3 className="font-semibold mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-primary-500" />
            Conversion Activity (7 days)
          </h3>
          {stats.daily_conversions.length > 0 ? (
            <div className="flex items-end justify-between h-40 gap-1">
              {stats.daily_conversions.map((day) => {
                const maxCount = Math.max(...stats.daily_conversions.map(d => d.count), 1);
                const height = (day.count / maxCount) * 100;
                return (
                  <div key={day.date} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-xs text-[hsl(var(--muted-foreground))]">{day.count}</span>
                    <div
                      className="w-full rounded-t-lg bg-gradient-to-t from-primary-500 to-purple-500 min-h-[4px] transition-all"
                      style={{ height: `${Math.max(height, 4)}%` }}
                    />
                    <span className="text-[10px] text-[hsl(var(--muted-foreground))]">
                      {new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-40 flex items-center justify-center text-[hsl(var(--muted-foreground))]">
              No conversion data yet
            </div>
          )}
        </motion.div>

        {/* Top Conversion Types */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="p-6 rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]"
        >
          <h3 className="font-semibold mb-4 flex items-center">
            <ArrowRightLeft className="w-5 h-5 mr-2 text-primary-500" />
            Top Conversions
          </h3>
          {stats.conversions_by_type.length > 0 ? (
            <div className="space-y-3">
              {stats.conversions_by_type.map((item) => {
                const maxCount = Math.max(...stats.conversions_by_type.map(c => c.count), 1);
                const pct = (item.count / maxCount) * 100;
                return (
                  <div key={item.conversion_type}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="font-medium">{item.conversion_type.replace(/_/g, ' → ').toUpperCase()}</span>
                      <span className="text-[hsl(var(--muted-foreground))]">{item.count}</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-[hsl(var(--muted))] overflow-hidden">
                      <div className="h-full rounded-full bg-gradient-to-r from-primary-500 to-purple-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-40 flex items-center justify-center text-[hsl(var(--muted-foreground))]">
              No conversions yet. Start converting!
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div>
      <div className="h-8 w-48 rounded-lg shimmer mb-2" />
      <div className="h-5 w-72 rounded-lg shimmer mb-8" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 rounded-2xl shimmer" />
        ))}
      </div>
      <div className="h-24 rounded-2xl shimmer mb-8" />
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="h-64 rounded-2xl shimmer" />
        <div className="h-64 rounded-2xl shimmer" />
      </div>
    </div>
  );
}
