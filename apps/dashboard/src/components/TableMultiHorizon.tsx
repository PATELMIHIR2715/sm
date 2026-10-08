import React from 'react';
import type { MultiHorizonAccuracy } from '../data/benchmarkData';
import { Target, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

interface TableMultiHorizonProps {
  data: MultiHorizonAccuracy[];
}

export const TableMultiHorizon: React.FC<TableMultiHorizonProps> = ({ data }) => {
  const renderHitBadge = (hitStatus: string) => {
    if (hitStatus.includes('YES') || hitStatus.includes('EXACT')) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">
          <CheckCircle2 className="w-2.5 h-2.5 mr-1" />
          HIT
        </span>
      );
    } else if (hitStatus.includes('LOSS') || hitStatus.includes('WRONG')) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-50 text-red-700 border border-red-200 font-mono">
          <XCircle className="w-2.5 h-2.5 mr-1" />
          STOPPED
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200 font-mono">
          <AlertCircle className="w-2.5 h-2.5 mr-1" />
          UNDER
        </span>
      );
    }
  };

  return (
    <div className="bg-white rounded-xl overflow-hidden border border-slate-200 shadow-xs">
      <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Target className="w-3.5 h-3.5 text-blue-600" />
            Table 2: 1-Day Target Accuracy & Hit Tracking (T+1)
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Compares predicted 1-day (T+1 / Tomorrow) ATR magnitude bounds against actual subsequent closing candles.
          </p>
        </div>
        <span className="text-[11px] font-mono text-slate-600 bg-slate-50 px-2.5 py-0.5 rounded-md border border-slate-200 self-start sm:self-auto font-semibold">
          {data.length} Signals Evaluated
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-750">
          <thead className="bg-slate-50 text-slate-500 uppercase font-mono text-[10px] tracking-wider border-b border-slate-200">
            <tr>
              <th className="py-2.5 px-3">Date & Stock</th>
              <th className="py-2.5 px-3">Corporate Catalyst</th>
              <th className="py-2.5 px-3">Prediction</th>
              <th className="py-2.5 px-3">1-Day (T+1) Target / Actual</th>
              <th className="py-2.5 px-3">T+1 Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-sans">
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-50/80 transition">
                <td className="py-3 px-3 whitespace-nowrap">
                  <div className="font-mono font-bold text-slate-900">{row.symbol}</div>
                  <div className="text-[10px] text-slate-400 font-mono">{row.date}</div>
                </td>
                <td className="py-3 px-3 max-w-xs">
                  <p className="line-clamp-2 text-slate-700 text-xs leading-snug">{row.headline}</p>
                </td>
                <td className="py-3 px-3 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                      row.predicted_direction === 'BULLISH'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-red-50 text-red-700 border border-red-200'
                    }`}
                  >
                    {row.predicted_direction}
                  </span>
                </td>
                <td className="py-3 px-3 font-mono whitespace-nowrap">
                  <div className="text-slate-800 font-medium">{row.t1_target_range}</div>
                  <div className={`text-[11px] font-bold ${row.actual_t1_move_pct >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    Actual: {row.actual_t1_move_pct >= 0 ? '+' : ''}{row.actual_t1_move_pct.toFixed(2)}%
                  </div>
                </td>
                <td className="py-3 px-3 whitespace-nowrap">
                  {renderHitBadge(row.t1_hit_status)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
