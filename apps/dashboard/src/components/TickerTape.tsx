import React from 'react';
import { Cpu, ShieldCheck, Database } from 'lucide-react';

interface TickerTapeProps {
  latencyMs?: number;
  signalsSec?: number;
  archetypesCount?: number;
  autoSyncActive?: boolean;
}

export const TickerTape: React.FC<TickerTapeProps> = ({
  latencyMs = 13.047,
  signalsSec = 76.6,
  archetypesCount = 200,
  autoSyncActive = true,
}) => {
  const marketIndices = [
    { name: 'NIFTY 50', value: '25,810.85', change: '+0.42%', isPos: true },
    { name: 'BANK NIFTY', value: '54,230.10', change: '+0.58%', isPos: true },
    { name: 'INDIA VIX', value: '12.85', change: '-3.40%', isPos: true },
    { name: 'NIFTY AUTO', value: '26,450.20', change: '+0.92%', isPos: true },
    { name: 'NIFTY DEFENSE', value: '7,890.40', change: '+2.40%', isPos: true },
    { name: 'BRENT CRUDE', value: '$74.80', change: '+1.63%', isPos: false },
    { name: 'USD/INR', value: '83.62', change: '-0.05%', isPos: true },
  ];

  return (
    <div className="bg-slate-100/90 border-b border-slate-200 text-xs py-1.5 px-3 sm:px-4 overflow-x-auto select-none scrollbar-none">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 sm:gap-6 min-w-max">
        {/* Market Indices Stream */}
        <div className="flex items-center gap-2.5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold shrink-0">
            MARKET:
          </span>

          <div className="flex items-center gap-2 text-[11px] font-mono">
            {marketIndices.map((idx, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 bg-white px-2 py-0.5 rounded-md border border-slate-200 text-slate-800 shadow-2xs shrink-0"
              >
                <span className="text-slate-500 font-medium">{idx.name}</span>
                <span className="text-slate-900 font-bold">{idx.value}</span>
                <span
                  className={`text-[10px] font-bold ${
                    idx.isPos ? 'text-emerald-600' : 'text-red-600'
                  }`}
                >
                  {idx.change}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Real-Time Engine Telemetry Stats */}
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-600 shrink-0">
          <div className="flex items-center gap-1 bg-white px-2 py-0.5 rounded-md border border-slate-200 text-slate-800 shadow-2xs">
            <Cpu className="w-3 h-3 text-blue-600" />
            <span>{latencyMs}ms ({signalsSec}/s)</span>
          </div>

          <div className="flex items-center gap-1 bg-white px-2 py-0.5 rounded-md border border-slate-200 text-slate-800 shadow-2xs hidden md:flex">
            <Database className="w-3 h-3 text-purple-600" />
            <span>{archetypesCount}+ RAG</span>
          </div>

          <div className="flex items-center gap-1 bg-white px-2 py-0.5 rounded-md border border-slate-200 text-slate-800 shadow-2xs hidden lg:flex">
            <ShieldCheck className="w-3 h-3 text-emerald-600" />
            <span>Zero Lookahead</span>
          </div>

          {autoSyncActive && (
            <div className="flex items-center gap-1 bg-white px-2 py-0.5 rounded-md border border-slate-200 text-slate-600 shadow-2xs">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>10s Poll</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
