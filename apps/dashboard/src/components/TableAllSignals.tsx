import React from 'react';
import type { IngestedSignal } from '../data/benchmarkData';
import { Filter, CheckCircle, AlertTriangle } from 'lucide-react';

interface TableAllSignalsProps {
  signals: IngestedSignal[];
}

export const TableAllSignals: React.FC<TableAllSignalsProps> = ({ signals }) => {
  return (
    <div className="bg-white rounded-xl overflow-hidden border border-slate-200 shadow-xs">
      <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-blue-600" />
            Table 1: Ingested News Signals (Raw Stream & Noise Filtering)
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Every corporate event captured by the pipeline. Signals passed to execution vs unverified rumors filtered out.
          </p>
        </div>
        <span className="text-[11px] font-mono text-slate-600 bg-slate-50 px-2.5 py-0.5 rounded-md border border-slate-200 self-start sm:self-auto font-semibold">
          {signals.length} Signals Captured
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-800">
          <thead className="bg-slate-50 text-slate-500 uppercase font-mono text-[10px] tracking-wider border-b border-slate-200">
            <tr>
              <th className="py-2.5 px-3">Timeline / Day</th>
              <th className="py-2.5 px-3">Stock & Source</th>
              <th className="py-2.5 px-3">Corporate Announcement</th>
              <th className="py-2.5 px-3">Direction</th>
              <th className="py-2.5 px-3">Conviction</th>
              <th className="py-2.5 px-3">Filter Outcome</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-sans">
            {signals.map((sig) => {
              const isUseful = sig.is_confirmed;
              return (
                <tr key={sig.id} className="hover:bg-slate-50/80 transition">
                  <td className="py-3 px-3 whitespace-nowrap">
                    <div className="font-bold text-slate-900 font-mono">{sig.date}</div>
                    <div className="text-[10px] text-slate-400 font-mono">{sig.time} &bull; {sig.day}</div>
                  </td>

                  <td className="py-3 px-3 whitespace-nowrap">
                    <div className="font-bold text-slate-900 font-mono">{sig.symbol}</div>
                    <div className="text-[10px] text-slate-500">{sig.company_name}</div>
                    <span className="inline-block mt-0.5 text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                      {sig.source_type}
                    </span>
                  </td>

                  <td className="py-3 px-3 max-w-md">
                    <p className="line-clamp-2 text-slate-700 text-xs leading-snug">{sig.headline}</p>
                  </td>

                  <td className="py-3 px-3 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                        sig.initial_direction === 'BULLISH'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : sig.initial_direction === 'BEARISH'
                          ? 'bg-red-50 text-red-700 border border-red-200'
                          : 'bg-slate-100 text-slate-700 border border-slate-200'
                      }`}
                    >
                      {sig.initial_direction}
                    </span>
                  </td>

                  <td className="py-3 px-3 whitespace-nowrap font-mono font-bold text-slate-900">
                    {sig.confidence_pct.toFixed(0)}%
                  </td>

                  <td className="py-3 px-3 whitespace-nowrap">
                    {isUseful ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">
                        <CheckCircle className="w-2.5 h-2.5 mr-1" />
                        PASSED FILTER
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 font-mono">
                        <AlertTriangle className="w-2.5 h-2.5 mr-1" />
                        NOISE FILTERED
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
