import React, { useState } from 'react';
import { X, TrendingUp, TrendingDown, Target, DollarSign, Smartphone, CheckCircle, Calendar } from 'lucide-react';
import type { LiveSignal } from '../data/benchmarkData';

interface SignalDetailModalProps {
  signal: LiveSignal | null;
  onClose: () => void;
  onOpenKellyModal?: () => void;
}

export const SignalDetailModal: React.FC<SignalDetailModalProps> = ({
  signal,
  onClose,
  onOpenKellyModal,
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  if (!signal) return null;

  const isBull = signal.predicted_direction === 'BULLISH';

  const handleCopyAlert = () => {
    const text = `🚨 *NIFTY 500 AI ALERT: ${signal.symbol}*
📊 *Direction:* ${signal.predicted_direction} (Conviction: ${signal.conviction_score_pct}%)
🏢 *Company:* ${signal.company_name} (${signal.sector})
📰 *Headline:* ${signal.headline}
💰 *Base LTP:* ₹${signal.current_base_price_inr?.toFixed(2)}
🎯 *1-Day Target (Tomorrow):* ${signal.t1_target.price_target_range_inr} (${signal.t1_target.percentage_range})
🛑 *Stop Loss:* ${signal.recommended_stop_loss}
💼 *Kelly Allocation:* ₹${signal.allocated_capital_inr?.toLocaleString('en-IN')} (${signal.shares_qty} shares)
⚡ *Strategy:* ${signal.recommended_strategy}`;

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-4 sm:p-6 shadow-2xl space-y-4 my-auto">
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-slate-200 pb-3.5">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xl font-bold font-mono text-slate-900">{signal.symbol}</span>
              <span
                className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${
                  isBull
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-red-50 text-red-700 border-red-200'
                }`}
              >
                {isBull ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {signal.predicted_direction}
              </span>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200">
                {signal.confluence_grade || 'A+ (CONFLUENCE)'}
              </span>
            </div>
            <p className="text-xs text-slate-500 font-sans mt-0.5">
              {signal.company_name} &bull; {signal.sector} &bull; Base Price: ₹{signal.current_base_price_inr?.toFixed(2)}
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-800 border border-slate-200 transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Regulatory News Announcement Card */}
        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1.5">
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 uppercase tracking-wider font-semibold">
            <span className="flex items-center gap-1 text-slate-700">
              <Calendar className="w-3 h-3 text-blue-600" />
              {signal.news_date || 'Sep 28, 2026'} @ {signal.news_time || '10:20 AM IST'}
            </span>
            <span className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
              {signal.source_type || 'NSE_FILING'}
            </span>
          </div>
          <p className="text-xs font-medium text-slate-900 leading-relaxed font-sans">
            "{signal.headline}"
          </p>
          {signal.materiality_ratio > 0 && (
            <div className="text-[10px] font-mono text-slate-500 pt-0.5">
              Contract Materiality: {(signal.materiality_ratio * 100).toFixed(1)}% of Annual Revenue
            </div>
          )}
        </div>

        {/* Microstructure Defense & Execution Parameters */}
        {(signal.execution_order_type || (signal.applied_mitigations && signal.applied_mitigations.length > 0)) && (
          <div className="bg-slate-50 p-3.5 rounded-xl border border-emerald-200 space-y-2 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
              <span className="text-emerald-700 font-bold flex items-center gap-1 text-[11px] uppercase">
                🛡️ Microstructure Defense Active
              </span>
              {signal.execution_order_type && (
                <span className="px-2 py-0.5 rounded bg-white text-slate-800 border border-slate-200 text-[10px] font-semibold">
                  Order: {signal.execution_order_type}
                </span>
              )}
            </div>

            {signal.optimal_entry_price && signal.optimal_entry_price !== signal.current_base_price_inr && (
              <div className="text-[11px] text-slate-800">
                <span className="text-slate-500">Optimal Entry Target:</span> ₹{signal.optimal_entry_price.toFixed(2)} (VWAP Pullback Buffer)
              </div>
            )}

            {signal.applied_mitigations && signal.applied_mitigations.length > 0 && (
              <div className="space-y-1 pt-1">
                <span className="text-[10px] text-slate-500 uppercase font-semibold">Enforced Risk Mitigations:</span>
                {signal.applied_mitigations.map((m, idx) => (
                  <div key={idx} className="text-[11px] text-slate-700 pl-3 flex items-start gap-1.5">
                    <span className="text-emerald-600 font-bold">&bull;</span>
                    <span>{m}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Catalyst Absorption Breakdown */}
            {signal.catalyst_absorption_pct !== undefined && signal.catalyst_absorption_pct > 0 && (
              <div className="mt-2 pt-2 border-t border-slate-200 bg-white p-2.5 rounded-lg border">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Catalyst Realized Move:</span>
                  <span className={`font-bold ${signal.catalyst_absorption_pct >= 75 ? 'text-red-600' : 'text-amber-600'}`}>
                    {signal.catalyst_absorption_pct.toFixed(1)}% Absorbed
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] mt-1">
                  <span className="text-slate-500">Remaining T+1 Alpha:</span>
                  <span className="font-bold text-emerald-600">
                    +{signal.remaining_alpha_pct?.toFixed(2)}% Available Upside
                  </span>
                </div>
                {signal.catalyst_absorption_pct >= 75 && (
                  <div className="mt-1.5 text-[10px] text-red-700 bg-red-50 p-1.5 rounded border border-red-200">
                    ⚠️ DO NOT CHASE: The intraday rally already reached the T+1 target corridor at market open. Entering at current market price risks buying the morning spike.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* 1-Day Price Target Corridor (T+1) */}
        <div>
          <div className="text-[11px] font-mono text-slate-500 uppercase tracking-wider mb-2 flex items-center justify-between font-semibold">
            <span className="flex items-center gap-1.5 text-slate-900 font-bold">
              <Target className="w-3.5 h-3.5 text-blue-600" />
              1-Day Price Target (Base: ₹{signal.current_base_price_inr?.toFixed(2)})
            </span>
            <span className="text-red-600 font-bold">
              SL: {signal.recommended_stop_loss}
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 flex items-center justify-between font-mono">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-100/70 text-blue-600 flex items-center justify-center shrink-0">
                <Target className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-800">
                  T+1 Tomorrow Target Corridor
                </div>
                <div className="text-[10px] text-slate-500">
                  Deadline: {signal.t1_target.target_date_horizon}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-base font-bold text-slate-900">
                {signal.t1_target.price_target_range_inr}
              </div>
              <div className="text-xs font-bold text-emerald-600">
                {signal.t1_target.percentage_range}
              </div>
            </div>
          </div>
        </div>

        {/* Kelly Sizing & Action Desk */}
        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2.5 font-mono">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <DollarSign className="w-3.5 h-3.5 text-blue-600" />
              Model Portfolio Allocation
            </span>
            <span className="text-xs text-slate-600 font-semibold">
              {signal.recommended_strategy}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-3 text-xs">
            <div>
              <div className="text-slate-500 text-[10px] font-semibold">Position Size:</div>
              <div className="text-xs font-bold text-slate-900 mt-0.5">
                ₹{signal.allocated_capital_inr?.toLocaleString('en-IN')}
              </div>
            </div>

            <div>
              <div className="text-slate-500 text-[10px] font-semibold">Shares:</div>
              <div className="text-xs font-bold text-slate-700 mt-0.5">
                {signal.shares_qty || 4} Qty
              </div>
            </div>

            <div>
              <div className="text-slate-500 text-[10px] font-semibold">Conviction:</div>
              <div className="text-xs font-bold text-emerald-600 mt-0.5">
                {signal.conviction_score_pct}%
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-1">
          {onOpenKellyModal && (
            <button
              onClick={onOpenKellyModal}
              className="text-xs font-mono text-blue-600 hover:text-blue-700 font-bold underline transition cursor-pointer"
            >
              Adjust Size in Kelly Desk →
            </button>
          )}

          <div className="flex items-center gap-2 ml-auto">
            <button
              onClick={handleCopyAlert}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white shadow-xs transition cursor-pointer"
            >
              {copied ? (
                <>
                  <CheckCircle className="w-3.5 h-3.5 text-white" />
                  <span>Copied Alert!</span>
                </>
              ) : (
                <>
                  <Smartphone className="w-3.5 h-3.5 text-white" />
                  <span>Copy Alert</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
