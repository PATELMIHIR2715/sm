import React from 'react';

interface LiveProgressProps {
  total: number;
  completed: number;
  remaining: number;
  progressPct: number;
  currentSymbol: string;
  currentHeadline: string;
  status: string;
  lastUpdated: string;
}

export const LiveProgressCard: React.FC<LiveProgressProps> = ({
  total,
  completed,
  remaining,
  progressPct,
  currentSymbol,
  currentHeadline,
  status,
  lastUpdated
}) => {
  return (
    <div className="bg-white rounded-xl p-3.5 sm:p-4 border border-slate-200 shadow-xs">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        {/* Left: Status & Description */}
        <div className="space-y-1 max-w-2xl">
          <div className="flex items-center space-x-2 flex-wrap">
            <span className="flex h-2 w-2 relative">
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800 font-mono">
              {status === 'COMPLETED' ? 'PIPELINE CALIBRATION COMPLETED' : 'CALIBRATING REAL-TIME SIGNALS'}
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              &bull; Synced {lastUpdated || 'Just now'}
            </span>
          </div>

          <p className="text-xs text-slate-600 font-normal leading-relaxed">
            <span className="text-slate-900 font-mono font-bold mr-1.5">{currentSymbol ? `[${currentSymbol}]` : ''}</span>
            {currentHeadline || 'Analyzing real-time stock filings & multi-horizon volatility bounds...'}
          </p>
        </div>

        {/* Right: Counter Badges */}
        <div className="flex items-center gap-2 self-start lg:self-auto">
          <div className="bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-center min-w-[70px]">
            <div className="text-[10px] text-slate-500 font-mono uppercase font-semibold">Done</div>
            <div className="text-sm font-bold text-emerald-600 font-mono">{completed}</div>
          </div>
          <div className="bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-center min-w-[70px]">
            <div className="text-[10px] text-slate-500 font-mono uppercase font-semibold">Pending</div>
            <div className="text-sm font-bold text-slate-400 font-mono">{remaining}</div>
          </div>
          <div className="bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-center min-w-[70px]">
            <div className="text-[10px] text-slate-500 font-mono uppercase font-semibold">Total</div>
            <div className="text-sm font-bold text-slate-900 font-mono">{total}</div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-3 space-y-1">
        <div className="flex justify-between text-[11px] font-mono text-slate-500">
          <span>Execution Pipeline</span>
          <span className="text-slate-900 font-bold">{progressPct.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden border border-slate-200">
          <div
            className="bg-emerald-500 h-full rounded-full transition-all duration-300 ease-out"
            style={{ width: `${Math.min(100, Math.max(0, progressPct))}%` }}
          />
        </div>
      </div>
    </div>
  );
};
