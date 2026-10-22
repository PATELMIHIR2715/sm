import React, { useState, useEffect } from 'react';
import { Target, CheckCircle2, AlertTriangle, TrendingUp, RefreshCw, Activity, ArrowUpRight, ArrowDownRight, Layers } from 'lucide-react';
import { API_BASE } from '../config';

interface LedgerItem {
  id: string;
  symbol: string;
  company_name: string;
  sector: string;
  direction: string;
  conviction_pct: number;
  version?: string;
  entry_ltp: number;
  current_ltp: number;
  target_range: string;
  stop_loss: string;
  max_move_pct: number;
  status: 'TARGET_HIT' | 'TARGET_NEAR' | 'STOPPED_OUT' | 'IN_PROGRESS';
  time: string;
  risk_reward: string;
}

interface VersionComparison {
  active_version: string;
  previous_version: string;
  active_accuracy_pct: number;
  previous_accuracy_pct: number;
  delta_pct: number;
  status: 'IMPROVED' | 'DECREASED' | 'MAINTAINED';
  is_degraded: boolean;
  alert_message: string;
}

interface VersionStats {
  version: string;
  name: string;
  description: string;
  target_strategy: string;
  total_signals: number;
  resolved_count: number;
  targets_hit: number;
  targets_near: number;
  stopped_out: number;
  in_progress: number;
  accuracy_rate_pct: number;
  pure_hit_rate_pct: number;
}

interface AccuracyMetrics {
  last_updated: string;
  active_version?: string;
  total_actionable_signals: number;
  total_evaluated_in_sample: number;
  resolved_count: number;
  targets_hit: number;
  targets_near: number;
  stopped_out: number;
  in_progress: number;
  accuracy_rate_pct: number;
  pure_hit_rate_pct: number;
  profit_factor: number;
  avg_risk_reward: string;
  version_comparison?: VersionComparison;
  version_breakdown?: Record<string, VersionStats>;
  ledger: LedgerItem[];
}

export const LiveAccuracyLedgerCard: React.FC = () => {
  const [metrics, setMetrics] = useState<AccuracyMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [selectedVersionFilter, setSelectedVersionFilter] = useState<string>('ALL');

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/accuracy-meter`);
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (e) {
      console.warn('Could not fetch accuracy meter:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!metrics) return null;

  const comparison = metrics.version_comparison;
  const breakdown = metrics.version_breakdown || {};
  const activeVer = metrics.active_version || 'v3.0';

  const filteredLedger = metrics.ledger.filter((item) => {
    if (selectedVersionFilter === 'ALL') return true;
    return (item.version || 'v3.0') === selectedVersionFilter;
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-lg my-4 text-slate-100">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-blue-500/10 border border-blue-500/20 rounded-xl">
            <Target className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-bold text-sm sm:text-base tracking-tight text-white">
                Live Hit-Rate Ledger & Accuracy Tracker
              </h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                Engine {activeVer} (Active)
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Ground-Truth OHLC
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Continuously tracks target accuracy and monitors performance shifts across model versions (v1, v2, v3)
            </p>
          </div>
        </div>

        {/* Global Hit Rate Badge */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
            <div className="text-right">
              <div className="text-xs font-mono font-bold text-emerald-400">
                {metrics.accuracy_rate_pct.toFixed(1)}% Accuracy Rate
              </div>
              <div className="text-[10px] font-mono text-slate-400">
                {metrics.targets_hit} Hits / {metrics.resolved_count} Resolved
              </div>
            </div>
          </div>

          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
            title="Refresh Evaluation"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Version Regression / Improvement Alert Banner */}
      {comparison && (
        <div
          className={`mt-3 p-3 rounded-xl border flex items-center justify-between gap-3 text-xs font-mono ${
            comparison.is_degraded
              ? 'bg-rose-950/40 border-rose-500/50 text-rose-200'
              : 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
          }`}
        >
          <div className="flex items-center gap-2">
            {comparison.is_degraded ? (
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            ) : (
              <TrendingUp className="w-4 h-4 text-emerald-400 shrink-0" />
            )}
            <span className="font-semibold">{comparison.alert_message}</span>
          </div>

          <div className="flex items-center gap-1.5 shrink-0 text-[11px]">
            <span className="text-slate-400">Delta vs {comparison.previous_version}:</span>
            <span
              className={`font-bold px-2 py-0.5 rounded-md flex items-center gap-0.5 ${
                comparison.is_degraded
                  ? 'bg-rose-500/20 text-rose-300'
                  : 'bg-emerald-500/20 text-emerald-300'
              }`}
            >
              {comparison.is_degraded ? (
                <ArrowDownRight className="w-3.5 h-3.5" />
              ) : (
                <ArrowUpRight className="w-3.5 h-3.5" />
              )}
              {comparison.delta_pct > 0 ? `+${comparison.delta_pct}%` : `${comparison.delta_pct}%`}
            </span>
          </div>
        </div>
      )}

      {/* Multi-Version Performance Comparison Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 my-3.5">
        {['v1.0', 'v2.0', 'v3.0'].map((vKey) => {
          const v = breakdown[vKey];
          if (!v) return null;
          const isActive = vKey === activeVer;
          return (
            <div
              key={vKey}
              onClick={() => setSelectedVersionFilter(selectedVersionFilter === vKey ? 'ALL' : vKey)}
              className={`p-3 rounded-xl border transition cursor-pointer ${
                selectedVersionFilter === vKey
                  ? 'bg-blue-950/40 border-blue-500 ring-1 ring-blue-500'
                  : isActive
                  ? 'bg-slate-800/80 border-blue-500/40 hover:bg-slate-800'
                  : 'bg-slate-800/40 border-slate-700/60 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-white flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-blue-400" />
                  {v.name}
                </span>
                {isActive && (
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    ACTIVE
                  </span>
                )}
              </div>

              <div className="mt-2 flex items-baseline justify-between">
                <div className="text-xl font-bold font-mono text-emerald-400">
                  {v.accuracy_rate_pct.toFixed(1)}%
                </div>
                <div className="text-[11px] font-mono text-slate-400">
                  {v.targets_hit} hits / {v.resolved_count} resolved
                </div>
              </div>

              <div className="mt-1 text-[10px] text-slate-400 font-mono truncate">
                Strategy: {v.target_strategy || 'Corridor'}
              </div>
            </div>
          );
        })}
      </div>

      {/* Metric Counters Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-3.5">
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-2.5">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Target Hits</div>
          <div className="text-lg font-bold font-mono text-emerald-400 mt-1 flex items-baseline gap-1.5">
            {metrics.targets_hit}
            <span className="text-[11px] font-normal text-slate-400">({metrics.pure_hit_rate_pct.toFixed(1)}% pure)</span>
          </div>
        </div>

        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-2.5">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Near Hits (75%+)</div>
          <div className="text-lg font-bold font-mono text-sky-400 mt-1">
            {metrics.targets_near}
          </div>
        </div>

        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-2.5">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Avg Risk/Reward</div>
          <div className="text-lg font-bold font-mono text-blue-400 mt-1">
            {metrics.avg_risk_reward}
          </div>
        </div>

        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-2.5">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Active In-Flight</div>
          <div className="text-lg font-bold font-mono text-amber-400 mt-1 flex items-baseline gap-1.5">
            {metrics.in_progress}
            <span className="text-[11px] font-normal text-slate-400">trades</span>
          </div>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="mt-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-slate-400 font-mono mb-2">
          <div className="flex items-center gap-1.5">
            <span>FILTER BY VERSION:</span>
            {['ALL', 'v3.0', 'v2.0', 'v1.0'].map((f) => (
              <button
                key={f}
                onClick={() => setSelectedVersionFilter(f)}
                className={`px-2 py-0.5 rounded text-[10px] font-mono transition cursor-pointer ${
                  selectedVersionFilter === f
                    ? 'bg-blue-600 text-white font-bold'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {f === 'ALL' ? 'All (Top 30)' : f}
              </button>
            ))}
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-400 hover:text-blue-300 transition text-right cursor-pointer"
          >
            {isExpanded ? 'Collapse Ledger' : 'Expand Ledger'}
          </button>
        </div>

        {isExpanded && (
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="bg-slate-800/80 text-slate-400 border-b border-slate-700">
                  <th className="py-2 px-3 font-semibold">Symbol</th>
                  <th className="py-2 px-3 font-semibold">Version</th>
                  <th className="py-2 px-3 font-semibold">Dir</th>
                  <th className="py-2 px-3 font-semibold">Entry LTP</th>
                  <th className="py-2 px-3 font-semibold">Target Corridor</th>
                  <th className="py-2 px-3 font-semibold">R:R</th>
                  <th className="py-2 px-3 font-semibold">Max Move</th>
                  <th className="py-2 px-3 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-900/50">
                {filteredLedger.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-4 text-center text-slate-500 font-mono text-xs">
                      No trades found matching version filter: {selectedVersionFilter}
                    </td>
                  </tr>
                ) : (
                  filteredLedger.map((item) => (
                    <tr key={item.id || item.symbol} className="hover:bg-slate-800/40 transition">
                      <td className="py-2 px-3 font-bold text-white flex items-center gap-1.5">
                        <span>{item.symbol}</span>
                        <span className="text-[10px] font-normal text-slate-400 truncate max-w-[80px]">
                          {item.sector}
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold ${
                            item.version === 'v3.0'
                              ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                              : item.version === 'v2.0'
                              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                              : 'bg-slate-700/60 text-slate-400 border border-slate-600'
                          }`}
                        >
                          {item.version || 'v3.0'}
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            item.direction === 'BULLISH'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {item.direction}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-slate-300">₹{item.entry_ltp.toLocaleString('en-IN')}</td>
                      <td className="py-2 px-3 text-sky-300 font-semibold">{item.target_range}</td>
                      <td className="py-2 px-3 text-blue-400">{item.risk_reward}</td>
                      <td className="py-2 px-3 text-emerald-400 font-semibold">+{item.max_move_pct.toFixed(2)}%</td>
                      <td className="py-2 px-3 text-right">
                        {item.status === 'TARGET_HIT' && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                            TARGET HIT
                          </span>
                        )}
                        {item.status === 'TARGET_NEAR' && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/30">
                            <TrendingUp className="w-3 h-3 text-sky-400" />
                            NEAR TARGET
                          </span>
                        )}
                        {item.status === 'IN_PROGRESS' && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                            <Activity className="w-3 h-3 text-blue-400" />
                            IN FLIGHT
                          </span>
                        )}
                        {item.status === 'STOPPED_OUT' && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                            <AlertTriangle className="w-3 h-3 text-rose-400" />
                            STOPPED
                          </span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
