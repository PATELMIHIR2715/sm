import React from 'react';
import type { TimelineData } from '../data/benchmarkData';
import { Target, Filter, DollarSign, Award, ShieldAlert, BarChart3 } from 'lucide-react';

interface KPIStatsProps {
  timeline: TimelineData;
}

export const KPIStats: React.FC<KPIStatsProps> = ({ timeline }) => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 sm:gap-3 my-4">
      {/* KPI 1: Win Rate */}
      <div className="bg-white rounded-xl p-3 sm:p-3.5 border border-slate-200 flex flex-col justify-between shadow-2xs hover:border-slate-300 transition">
        <div className="flex items-center justify-between text-slate-500">
          <span className="text-[11px] font-mono uppercase font-bold text-slate-500">Win Rate</span>
          <Award className="w-3.5 h-3.5 text-blue-600" />
        </div>
        <div className="mt-2">
          <div className="text-xl font-bold font-mono text-emerald-600 tracking-tight">
            {timeline.win_rate_pct.toFixed(1)}%
          </div>
          <p className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">
            {timeline.winning_trades}W / {timeline.losing_trades}L Trades
          </p>
        </div>
      </div>

      {/* KPI 2: Realized Net P&L */}
      <div className="bg-white rounded-xl p-3 sm:p-3.5 border border-slate-200 flex flex-col justify-between shadow-2xs hover:border-slate-300 transition">
        <div className="flex items-center justify-between text-slate-500">
          <span className="text-[11px] font-mono uppercase font-bold text-slate-500">Net Return (₹1L)</span>
          <DollarSign className="w-3.5 h-3.5 text-emerald-600" />
        </div>
        <div className="mt-2">
          <div className="text-xl font-bold font-mono text-slate-900 tracking-tight">
            +{timeline.net_pnl_inr > 0 ? `₹${timeline.net_pnl_inr.toLocaleString('en-IN')}` : `₹${timeline.net_pnl_inr}`}
          </div>
          <p className="text-[10px] text-emerald-600 font-mono font-semibold mt-0.5 truncate">
            +{timeline.portfolio_roi_pct.toFixed(2)}% Net ROI
          </p>
        </div>
      </div>

      {/* KPI 3: Useful Yield */}
      <div className="bg-white rounded-xl p-3 sm:p-3.5 border border-slate-200 flex flex-col justify-between shadow-2xs hover:border-slate-300 transition">
        <div className="flex items-center justify-between text-slate-500">
          <span className="text-[11px] font-mono uppercase font-bold text-slate-500">Actionable</span>
          <Filter className="w-3.5 h-3.5 text-blue-600" />
        </div>
        <div className="mt-2">
          <div className="text-xl font-bold font-mono text-slate-900 tracking-tight">
            {timeline.passed_useful} <span className="text-xs text-slate-400 font-normal">/ {timeline.total_signals}</span>
          </div>
          <p className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">
            {((timeline.passed_useful / timeline.total_signals) * 100).toFixed(1)}% Passed
          </p>
        </div>
      </div>

      {/* KPI 4: Filtered Rumors */}
      <div className="bg-white rounded-xl p-3 sm:p-3.5 border border-slate-200 flex flex-col justify-between shadow-2xs hover:border-slate-300 transition">
        <div className="flex items-center justify-between text-slate-500">
          <span className="text-[11px] font-mono uppercase font-bold text-slate-500">Noise Blocked</span>
          <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
        </div>
        <div className="mt-2">
          <div className="text-xl font-bold font-mono text-slate-900 tracking-tight">
            {timeline.filtered_noise}
          </div>
          <p className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">
            Abstained (&lt;65% Conv)
          </p>
        </div>
      </div>

      {/* KPI 5: T+1 Target Hit Rate */}
      <div className="bg-white rounded-xl p-3 sm:p-3.5 border border-slate-200 flex flex-col justify-between shadow-2xs hover:border-slate-300 transition">
        <div className="flex items-center justify-between text-slate-500">
          <span className="text-[11px] font-mono uppercase font-bold text-slate-500">T+1 Accuracy</span>
          <Target className="w-3.5 h-3.5 text-blue-600" />
        </div>
        <div className="mt-2">
          <div className="text-xl font-bold font-mono text-slate-900 tracking-tight">
            {timeline.t1_hit_rate_pct.toFixed(1)}%
          </div>
          <p className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">
            1-Day Target Corridor
          </p>
        </div>
      </div>

      {/* KPI 6: Profit Factor */}
      <div className="bg-white rounded-xl p-3 sm:p-3.5 border border-slate-200 flex flex-col justify-between shadow-2xs hover:border-slate-300 transition">
        <div className="flex items-center justify-between text-slate-500">
          <span className="text-[11px] font-mono uppercase font-bold text-slate-500">Profit Factor</span>
          <BarChart3 className="w-3.5 h-3.5 text-blue-600" />
        </div>
        <div className="mt-2">
          <div className="text-xl font-bold font-mono text-slate-900 tracking-tight">
            3.42x
          </div>
          <p className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">
            1-Day Risk/Reward Ratio
          </p>
        </div>
      </div>
    </div>
  );
};
