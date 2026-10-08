import React, { useState } from 'react';
import type { LiveSignal } from '../data/benchmarkData';
import { TrendingUp, TrendingDown, ShieldCheck, Calendar, Clock, Flame, Award, ExternalLink, Calculator } from 'lucide-react';
import { SignalDetailModal } from './SignalDetailModal';
import { KellyCalculatorModal } from './KellyCalculatorModal';

interface TableTodayLiveProps {
  signals?: LiveSignal[];
}

export const TableTodayLive: React.FC<TableTodayLiveProps> = ({ signals = [] }) => {
  const [selectedSignal, setSelectedSignal] = useState<LiveSignal | null>(null);
  const [isKellyModalOpen, setIsKellyModalOpen] = useState<boolean>(false);
  const [activeKellySymbol, setActiveKellySymbol] = useState<string>('HAL');
  const [activeKellyLtp, setActiveKellyLtp] = useState<number>(4738.0);

  if (!signals || signals.length === 0) {
    return (
      <div className="bg-white rounded-xl p-8 text-center text-slate-500 border border-slate-200 shadow-xs">
        <Flame className="w-6 h-6 mx-auto text-slate-400 mb-2" />
        <p className="text-sm font-semibold text-slate-700">No live forward signals active for this selected historical backtest timeline.</p>
        <p className="text-xs text-slate-500 mt-1">Select the "Live Cycle (Sep 18 – 28, 2026)" timeline to view today's active forward predictions.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3.5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-sm sm:text-base font-bold text-slate-900 flex items-center gap-2">
            <Flame className="w-4 h-4 text-blue-600" />
            Live Signals & Forward Multi-Horizon Target Projections
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Active corporate catalysts with exact news timestamps, dynamic Kelly allocation, and multi-horizon target deadlines.
          </p>
        </div>
        <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 self-start sm:self-auto">
          {signals.length} Active Setups
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        {signals.map((sig) => {
          const isBull = sig.predicted_direction === 'BULLISH';

          return (
            <div
              key={sig.id}
              onClick={() => setSelectedSignal(sig)}
              className="bg-white rounded-xl p-4 sm:p-5 border border-slate-200 hover:border-blue-400 cursor-pointer flex flex-col justify-between transition duration-150 shadow-2xs hover:shadow-md"
            >
              {/* Card Header: Symbol, Price, Direction Badge */}
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-base font-bold text-slate-900 font-mono tracking-tight">
                        {sig.symbol}
                      </span>
                      <span className="text-xs text-slate-500 font-normal">
                        {sig.company_name}
                      </span>
                      <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200">
                        {sig.sector}
                      </span>
                    </div>

                    <div className="mt-1 flex flex-wrap items-baseline gap-2">
                      <span className="text-lg font-bold text-slate-900 font-mono">
                        ₹{sig.current_base_price_inr?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                      <span className={`text-xs font-mono font-bold ${(sig.day_change_pct || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                        {(sig.day_change_pct || 0) >= 0 ? '+' : ''}{sig.day_change_pct?.toFixed(2)}%
                      </span>
                      <span className="inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse" />
                        LIVE TICK
                      </span>
                      {sig.confluence_grade && (
                        <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200 font-mono">
                          <Award className="w-3 h-3 mr-1 text-blue-600" />
                          {sig.confluence_grade}
                        </span>
                      )}
                      {sig.execution_order_type && (
                        <span className={`inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-md border font-mono ${
                          sig.execution_order_type.includes('DO_NOT_CHASE') || sig.execution_order_type.includes('EXHAUSTED')
                            ? 'bg-red-50 text-red-700 border-red-200 font-bold animate-pulse'
                            : sig.execution_order_type.includes('LIMIT') 
                            ? 'bg-amber-50 text-amber-700 border-amber-200' 
                            : sig.execution_order_type.includes('ABSTAIN') || sig.execution_order_type.includes('FILTERED')
                            ? 'bg-red-50 text-red-700 border-red-200'
                            : 'bg-blue-50 text-blue-700 border-blue-200'
                        }`}>
                          <ShieldCheck className="w-3 h-3 mr-1" />
                          {sig.execution_order_type}
                        </span>
                      )}
                      {sig.catalyst_absorption_pct !== undefined && sig.catalyst_absorption_pct > 0 && (
                        <span className={`inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-md border font-mono ${
                          sig.catalyst_absorption_pct >= 75
                            ? 'bg-red-50 text-red-700 border-red-200'
                            : sig.catalyst_absorption_pct >= 40
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        }`}>
                          {sig.catalyst_absorption_pct >= 75 ? '⚡ 80%+ ABSORBED' : `${sig.catalyst_absorption_pct.toFixed(0)}% ABSORBED`}
                          {sig.remaining_alpha_pct !== undefined && (
                            <span className="ml-1 text-[9px] text-slate-500">
                              (+{sig.remaining_alpha_pct.toFixed(2)}% left)
                            </span>
                          )}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-mono font-bold ${
                        sig.execution_order_type?.includes('DO_NOT_CHASE')
                          ? 'bg-red-50 text-red-700 border border-red-200'
                          : isBull
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-red-50 text-red-700 border border-red-200'
                      }`}
                    >
                      {isBull ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                      {sig.predicted_direction} ({sig.conviction_score_pct.toFixed(0)}%)
                    </span>
                    <div className="text-[11px] font-mono text-slate-500 mt-1 max-w-xs font-medium">
                      {sig.recommended_strategy}
                    </div>
                  </div>
                </div>

                {/* Microstructure Defense Warnings & Applied Mitigations */}
                {sig.applied_mitigations && sig.applied_mitigations.length > 0 && (
                  <div className="mt-2 text-[11px] font-mono text-emerald-800 bg-emerald-50 px-2.5 py-1.5 rounded-lg border border-emerald-200 flex flex-col gap-0.5">
                    <div className="flex items-center gap-1.5 font-bold text-[10px] text-emerald-700 uppercase">
                      <ShieldCheck className="w-3 h-3 text-emerald-600" /> Microstructure Defense Active:
                    </div>
                    {sig.applied_mitigations.map((mitigation, idx) => (
                      <span key={idx} className="text-[10px] text-slate-700 pl-4">
                        &bull; {mitigation}
                      </span>
                    ))}
                  </div>
                )}

                {/* Target Confidence Note on Market Drag */}
                {sig.target_confidence_note && (
                  <div className="mt-2 text-[11px] font-mono text-slate-700 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200 flex items-center justify-between">
                    <span>Target Note: {sig.target_confidence_note}</span>
                    {sig.market_drag_contribution_pct !== undefined && (
                      <span className="text-slate-500 font-semibold">Index Drag: {sig.market_drag_contribution_pct > 0 ? '+' : ''}{sig.market_drag_contribution_pct}%</span>
                    )}
                  </div>
                )}

                {/* Enhanced Catalyst Card with Exact News Date & Time */}
                <div className="mt-2.5 text-xs text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-200 space-y-1.5">
                  <div className="flex flex-wrap items-center justify-between gap-1.5 border-b border-slate-200 pb-1">
                    <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-500">
                      <Calendar className="w-3 h-3 text-blue-600" />
                      <span>{sig.news_date || 'Sep 28, 2026'}</span>
                      <span className="text-slate-300">&bull;</span>
                      <Clock className="w-3 h-3 text-blue-600" />
                      <span>{sig.news_time || '10:20 AM IST'}</span>
                    </div>

                    {sig.source_type && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-white text-slate-600 border border-slate-200 font-semibold">
                        {sig.source_type}
                      </span>
                    )}
                  </div>

                  <p className="text-slate-900 leading-relaxed font-sans pt-0.5 text-xs">
                    <span className="text-blue-600 font-bold mr-1">Catalyst:</span>
                    {sig.headline}
                  </p>
                </div>
              </div>

              {/* 1-Day Target (T+1 / Tomorrow) */}
              <div className="mt-3 pt-2.5 border-t border-slate-200 space-y-2">
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 uppercase tracking-wider font-semibold">
                  <span>1-Day Target Horizon (Tomorrow):</span>
                  {sig.allocated_capital_inr && (
                    <span className="text-slate-900 font-mono normal-case font-bold">
                      Kelly: ₹{sig.allocated_capital_inr.toLocaleString('en-IN')} ({sig.shares_qty} Qty)
                    </span>
                  )}
                </div>

                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-blue-100/70 text-blue-600 flex items-center justify-center shrink-0">
                      <Calendar className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-[11px] text-slate-800 font-mono font-bold">
                        T+1 Target (Tomorrow)
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        Deadline: {sig.t1_target.target_date_horizon}
                      </div>
                    </div>
                  </div>
                  <div className="text-right font-mono">
                    <div className="text-sm font-bold text-slate-900">
                      {sig.t1_target.price_target_range_inr}
                    </div>
                    <div className="text-xs font-bold text-emerald-600">
                      {sig.t1_target.percentage_range}
                    </div>
                  </div>
                </div>

                {/* Card Bottom Actions */}
                <div className="flex items-center justify-between text-xs pt-1">
                  <span className="text-red-600 font-mono text-[11px] font-semibold flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-red-600" /> Stop-Loss: {sig.recommended_stop_loss}
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveKellySymbol(sig.symbol);
                        setActiveKellyLtp(sig.current_base_price_inr);
                        setIsKellyModalOpen(true);
                      }}
                      className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 border border-slate-200 transition cursor-pointer"
                      title="Adjust Kelly Position Size"
                    >
                      <Calculator className="w-3.5 h-3.5 text-blue-600" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedSignal(sig);
                      }}
                      className="flex items-center gap-1 text-blue-600 hover:text-blue-700 font-mono text-[11px] font-bold cursor-pointer"
                    >
                      <span>Deep Dive</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Signal Detail Modal */}
      <SignalDetailModal
        signal={selectedSignal}
        onClose={() => setSelectedSignal(null)}
        onOpenKellyModal={() => {
          if (selectedSignal) {
            setActiveKellySymbol(selectedSignal.symbol);
            setActiveKellyLtp(selectedSignal.current_base_price_inr);
          }
          setSelectedSignal(null);
          setIsKellyModalOpen(true);
        }}
      />

      {/* Kelly Sizing Calculator Modal */}
      <KellyCalculatorModal
        isOpen={isKellyModalOpen}
        onClose={() => setIsKellyModalOpen(false)}
        defaultSymbol={activeKellySymbol}
        defaultLtp={activeKellyLtp}
      />
    </div>
  );
};
