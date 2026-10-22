import React, { useState, useMemo } from 'react';
import type { LiveSignal } from '../data/benchmarkData';
import { 
  TrendingUp, 
  TrendingDown, 
  ShieldCheck, 
  Calendar, 
  Clock, 
  Flame, 
  Award, 
  ChevronRight, 
  Calculator,
  ShieldAlert,
  AlertTriangle,
  Ban,
  Filter,
  CheckCircle2,
  Lock
} from 'lucide-react';
import { SignalDetailModal } from './SignalDetailModal';
import { KellyCalculatorModal } from './KellyCalculatorModal';

interface TableTodayLiveProps {
  signals?: LiveSignal[];
}

type TabMode = 'TRADABLE' | 'QUARANTINED' | 'ALL';

interface QuarantineInfo {
  badge: string;
  categoryTitle: string;
  bgBadge: string;
  iconType: 'shield-alert' | 'alert-triangle' | 'ban' | 'filter' | 'trending-down' | 'lock';
  description: string;
}

function getQuarantineDetails(sig: LiveSignal): QuarantineInfo {
  const status = sig.actionability_status || '';
  const reason = sig.suppression_reason || '';
  const preopenStatus = sig.preopen_status || '';

  if (status.includes('RISK_OFF') || status.includes('INSUFFICIENT_ALPHA')) {
    return {
      badge: 'QUARANTINED: RISK-OFF MARKET DRAG',
      categoryTitle: 'Broad Market Drag Veto',
      bgBadge: 'bg-amber-100 text-amber-900 border-amber-300',
      iconType: 'shield-alert',
      description: 'Terminally vetoed due to broader market selloff (Nifty/Sector drag). News alpha was insufficient to defend positive T+1 expected value.'
    };
  }
  if (status.includes('ADVERSE_PREOPEN_GAP') || preopenStatus === 'QUARANTINED') {
    const gapStr = sig.preopen_gap_pct !== undefined 
      ? `(${sig.preopen_gap_pct > 0 ? '+' : ''}${sig.preopen_gap_pct.toFixed(2)}% gap)`
      : '';
    return {
      badge: 'QUARANTINED: ADVERSE PRE-OPEN GAP',
      categoryTitle: 'Pre-Market Gap Trap Filter',
      bgBadge: 'bg-red-100 text-red-900 border-red-300',
      iconType: 'alert-triangle',
      description: `NSE 09:08 AM auction opened adversely ${gapStr}, wiping out the risk-reward ratio before opening bell. Live entry aborted.`
    };
  }
  if (status.includes('PREOPEN_GAP_EXHAUSTED')) {
    return {
      badge: 'QUARANTINED: TARGET EXHAUSTED OPEN',
      categoryTitle: 'Pre-Market Target Exhaustion',
      bgBadge: 'bg-amber-100 text-amber-900 border-amber-300',
      iconType: 'alert-triangle',
      description: 'Stock opened with massive gap directly into the T1 target zone. Zero statistical edge remaining to initiate new entry.'
    };
  }
  if (status.includes('SHORT_NOT_FNO') || status.includes('NON_EXECUTABLE_SHORT')) {
    return {
      badge: 'QUARANTINED: NON-F&O CASH SHORT',
      categoryTitle: 'Derivatives Constraint',
      bgBadge: 'bg-rose-100 text-rose-900 border-rose-300',
      iconType: 'ban',
      description: 'Cash-equity overnight short suppressed. Indian exchange regulations prohibit overnight short positions without verified F&O eligibility.'
    };
  }
  if (status.includes('ROUTINE_DIVIDEND') || status.includes('SELL_THE_NEWS')) {
    return {
      badge: 'QUARANTINED: SELL-THE-NEWS DIVIDEND',
      categoryTitle: 'Routine Corporate Action',
      bgBadge: 'bg-purple-100 text-purple-900 border-purple-300',
      iconType: 'trending-down',
      description: 'Routine dividend declaration filtered. Empirical data shows high vulnerability to sell-the-news profit-taking and ex-dividend drag.'
    };
  }
  if (status.includes('IMMATERIAL_ORDER')) {
    return {
      badge: 'QUARANTINED: IMMATERIAL ORDER (<3% SALES)',
      categoryTitle: 'Materiality Cutoff Failure',
      bgBadge: 'bg-slate-100 text-slate-800 border-slate-300',
      iconType: 'filter',
      description: 'Contract value is below the strict 3.0% annual revenue materiality hurdle. Filtered out as non-actionable corporate noise.'
    };
  }
  if (status.includes('PENNY') || status.includes('CIRP') || status.includes('INACTIVE') || status.includes('ILLIQUID') || status.includes('TURNOVER')) {
    return {
      badge: 'QUARANTINED: MICROSTRUCTURE & LIQUIDITY',
      categoryTitle: 'Microstructure Defense',
      bgBadge: 'bg-slate-100 text-slate-800 border-slate-300',
      iconType: 'ban',
      description: 'Terminally suppressed due to liquidity/turnover restrictions (< ₹2.0 Cr ADTV, penny price < ₹50, or CIRP insolvency blacklist).'
    };
  }
  if (status.includes('UNVERIFIED')) {
    return {
      badge: 'QUARANTINED: UNVERIFIED LIVE DATA',
      categoryTitle: 'Data Quality Fail-Closed',
      bgBadge: 'bg-slate-100 text-slate-800 border-slate-300',
      iconType: 'lock',
      description: 'Exchange quote or company fundamentals could not be verified from official market feeds. Zero synthetic fallback policy enforced.'
    };
  }

  return {
    badge: 'QUARANTINED: RISK CONTROLS ACTIVE',
    categoryTitle: 'Pipeline Risk Veto',
    bgBadge: 'bg-amber-100 text-amber-900 border-amber-300',
    iconType: 'shield-alert',
    description: reason || 'Signal terminally quarantined by quantitative risk and tradability gatekeepers.'
  };
}

const renderQuarantineIcon = (type: QuarantineInfo['iconType']) => {
  switch (type) {
    case 'alert-triangle':
      return <AlertTriangle className="w-3.5 h-3.5 mr-1 shrink-0" />;
    case 'ban':
      return <Ban className="w-3.5 h-3.5 mr-1 shrink-0" />;
    case 'filter':
      return <Filter className="w-3.5 h-3.5 mr-1 shrink-0" />;
    case 'lock':
      return <Lock className="w-3.5 h-3.5 mr-1 shrink-0" />;
    case 'trending-down':
      return <TrendingDown className="w-3.5 h-3.5 mr-1 shrink-0" />;
    default:
      return <ShieldAlert className="w-3.5 h-3.5 mr-1 shrink-0" />;
  }
};

export const TableTodayLive: React.FC<TableTodayLiveProps> = ({ signals = [] }) => {
  const [selectedSignal, setSelectedSignal] = useState<LiveSignal | null>(null);
  const [isKellyModalOpen, setIsKellyModalOpen] = useState<boolean>(false);
  const [activeKellySymbol, setActiveKellySymbol] = useState<string>('HAL');
  const [activeKellyLtp, setActiveKellyLtp] = useState<number>(4738.0);
  const [activeTab, setActiveTab] = useState<TabMode>('TRADABLE');

  const isTradableSignal = (sig: LiveSignal): boolean => {
    const status = sig.actionability_status || '';
    if (sig.is_useful === false || sig.dispatchable === false) return false;
    if (status.startsWith('SUPPRESSED') || status === 'INACTIVE_UNTRADABLE_STOCK') return false;
    if (sig.preopen_status === 'QUARANTINED' || sig.preopen_status === 'UNVERIFIED_PRICE_QUARANTINED') return false;
    return true;
  };

  const { tradableSignals, quarantinedSignals } = useMemo(() => {
    const tradable: LiveSignal[] = [];
    const quarantined: LiveSignal[] = [];

    signals.forEach(s => {
      if (isTradableSignal(s)) {
        tradable.push(s);
      } else {
        quarantined.push(s);
      }
    });

    return { tradableSignals: tradable, quarantinedSignals: quarantined };
  }, [signals]);

  const displayedSignals = useMemo(() => {
    if (activeTab === 'TRADABLE') return tradableSignals;
    if (activeTab === 'QUARANTINED') return quarantinedSignals;
    return signals;
  }, [activeTab, tradableSignals, quarantinedSignals, signals]);

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
    <div className="space-y-4">
      {/* Header and Filter Tabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
        <div>
          <h2 className="text-sm sm:text-base font-bold text-slate-900 flex items-center gap-2">
            <Flame className="w-4 h-4 text-blue-600" />
            Live Signals & Quantitative Execution Gatekeeper
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Strict institutional filters enforce pre-open verification, macro regime beta drag vetoes, and zero-loss quarantine rules.
          </p>
        </div>

        {/* Tab Filter Switcher */}
        <div className="inline-flex p-1 bg-slate-100 rounded-lg border border-slate-200 self-start md:self-auto">
          <button
            onClick={() => setActiveTab('TRADABLE')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono font-bold transition cursor-pointer ${
              activeTab === 'TRADABLE'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            Tradable Active ({tradableSignals.length})
          </button>

          <button
            onClick={() => setActiveTab('QUARANTINED')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono font-bold transition cursor-pointer ${
              activeTab === 'QUARANTINED'
                ? 'bg-amber-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Safety Quarantined ({quarantinedSignals.length})
          </button>

          <button
            onClick={() => setActiveTab('ALL')}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-mono font-bold transition cursor-pointer ${
              activeTab === 'ALL'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
            }`}
          >
            All ({signals.length})
          </button>
        </div>
      </div>

      {/* Empty State for Selected Tab */}
      {displayedSignals.length === 0 && (
        <div className="bg-white rounded-xl p-8 text-center text-slate-500 border border-slate-200 shadow-xs">
          {activeTab === 'TRADABLE' ? (
            <>
              <ShieldAlert className="w-8 h-8 mx-auto text-amber-500 mb-2" />
              <p className="text-sm font-bold text-slate-800">All candidate setups currently quarantined for capital preservation.</p>
              <p className="text-xs text-slate-500 mt-1">Review the "Safety Quarantined" tab to view the macro drag and gap reasons protecting your capital.</p>
            </>
          ) : (
            <>
              <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500 mb-2" />
              <p className="text-sm font-bold text-slate-800">No quarantined setups in this batch.</p>
              <p className="text-xs text-slate-500 mt-1">All processed signals met strict tradability and execution standards.</p>
            </>
          )}
        </div>
      )}

      {/* Signal Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        {displayedSignals.map((sig) => {
          const isBull = sig.predicted_direction === 'BULLISH';
          const isTradable = isTradableSignal(sig);
          const quarantine = !isTradable ? getQuarantineDetails(sig) : null;
          const isPreopenVerified = sig.preopen_status === 'APPROVED_FOR_EXECUTION';

          return (
            <div
              key={sig.id}
              onClick={() => setSelectedSignal(sig)}
              className={`bg-white rounded-xl p-4 sm:p-5 border cursor-pointer flex flex-col justify-between transition duration-150 shadow-2xs hover:shadow-md ${
                !isTradable 
                  ? 'border-amber-200 bg-amber-50/20 hover:border-amber-400' 
                  : 'border-slate-200 hover:border-blue-400'
              }`}
            >
              {/* Card Header: Symbol, Price, Status Badge */}
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

                      {/* Live Tick or Verification Badges */}
                      {isPreopenVerified ? (
                        <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 border border-emerald-300 font-mono">
                          <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-700" />
                          09:10 AM AUCTION VERIFIED
                          {sig.preopen_gap_pct !== undefined && (
                            <span className="ml-1 font-mono">({sig.preopen_gap_pct > 0 ? '+' : ''}{sig.preopen_gap_pct.toFixed(2)}%)</span>
                          )}
                        </span>
                      ) : (
                        <span className="inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse" />
                          LIVE TICK
                        </span>
                      )}

                      {sig.confluence_grade && isTradable && (
                        <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200 font-mono">
                          <Award className="w-3 h-3 mr-1 text-blue-600" />
                          {sig.confluence_grade}
                        </span>
                      )}

                      {((sig as any).risk_reward_ratio) && isTradable && (
                        <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 font-mono">
                          R:R {(sig as any).risk_reward_ratio}
                        </span>
                      )}

                      {((sig as any).circuit_warning) && (
                        <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-md bg-red-50 text-red-700 border border-red-300 font-mono animate-pulse">
                          {(sig as any).circuit_warning}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Right Header Status Pill */}
                  <div className="text-right shrink-0">
                    {quarantine ? (
                      <div>
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[11px] font-mono font-bold border ${quarantine.bgBadge}`}>
                          {renderQuarantineIcon(quarantine.iconType)}
                          {quarantine.badge}
                        </span>
                        <div className="text-[10px] font-mono text-slate-500 mt-1 font-semibold uppercase">
                          {quarantine.categoryTitle}
                        </div>
                      </div>
                    ) : (
                      <div>
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                            isBull
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-red-50 text-red-700 border border-red-200'
                          }`}
                        >
                          {isBull ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                          {sig.predicted_direction} ({sig.conviction_score_pct.toFixed(0)}%)
                        </span>
                        <div className="text-[11px] font-mono text-slate-500 mt-1 font-medium">
                          {sig.recommended_strategy}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Target Confidence Note / Market Drag Warning */}
                {sig.market_drag_contribution_pct !== undefined && sig.market_drag_contribution_pct !== 0 && (
                  <div className="mt-2 text-[11px] font-mono text-slate-700 bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-200 flex items-center justify-between">
                    <span className="flex items-center gap-1 font-semibold text-slate-600">
                      <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                      Macro Beta Drag:
                    </span>
                    <span className={`font-bold font-mono ${sig.market_drag_contribution_pct < 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                      {sig.market_drag_contribution_pct > 0 ? '+' : ''}{sig.market_drag_contribution_pct.toFixed(2)}%
                    </span>
                  </div>
                )}

                {/* News Catalyst Headline Box */}
                <div className="mt-2.5 text-xs text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-200 space-y-1.5">
                  <div className="flex flex-wrap items-center justify-between gap-1.5 border-b border-slate-200 pb-1">
                    <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-500">
                      <Calendar className="w-3 h-3 text-blue-600" />
                      <span>{sig.news_date || 'Oct 22, 2026'}</span>
                      <span className="text-slate-300">&bull;</span>
                      <Clock className="w-3 h-3 text-blue-600" />
                      <span>{sig.news_time || '09:08 AM IST'}</span>
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

              {/* Card Footer: Quarantined Notice vs Tradable Targets */}
              {!isTradable && quarantine ? (
                <div className="mt-3 pt-2.5 border-t border-amber-200">
                  <div className="bg-amber-50 p-3 rounded-lg border border-amber-200 flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono font-bold text-amber-900 flex items-center gap-1.5">
                        <ShieldAlert className="w-4 h-4 text-amber-700" />
                        CAPITAL PRESERVATION GATEKEEPER
                      </span>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-red-100 text-red-800 border border-red-200">
                        LIVE DISPATCH BLOCKED
                      </span>
                    </div>

                    <p className="text-xs text-amber-900 leading-normal font-sans">
                      {quarantine.description}
                    </p>

                    <div className="flex items-center justify-between text-xs pt-1 border-t border-amber-200/60 mt-1">
                      <span className="text-[10px] font-mono text-amber-800 font-semibold">
                        Capital Protected • Zero Execution Risk
                      </span>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedSignal(sig);
                        }}
                        className="flex items-center gap-1 text-blue-700 hover:text-blue-800 font-mono text-[11px] font-bold cursor-pointer"
                      >
                        Forensic Details <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="mt-3 pt-2.5 border-t border-slate-200 space-y-2">
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 uppercase tracking-wider font-semibold">
                    <span>1-Day Target Horizon (Tomorrow):</span>
                    {sig.allocated_capital_inr && (
                      <span className="text-slate-900 font-mono normal-case font-bold">
                        Kelly: ₹{sig.allocated_capital_inr.toLocaleString('en-IN')} ({sig.shares_qty} Qty)
                      </span>
                    )}
                  </div>

                  {(sig as any).two_tier_targets ? (
                    <div className="grid grid-cols-2 gap-2 font-mono">
                      <div className="bg-emerald-50/70 p-2 rounded-lg border border-emerald-200">
                        <div className="text-[10px] text-emerald-800 font-bold flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                          T1 Safe Profit-Lock
                        </div>
                        <div className="text-xs font-bold text-slate-900 mt-0.5">
                          ₹{Number((sig as any).two_tier_targets.t1_safe.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <div className="text-[10px] text-emerald-700 font-semibold">
                          {(sig as any).two_tier_targets.t1_safe.percentage} (Book 70%)
                        </div>
                      </div>

                      <div className="bg-blue-50/70 p-2 rounded-lg border border-blue-200">
                        <div className="text-[10px] text-blue-800 font-bold flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
                          T2 Breakout Runner
                        </div>
                        <div className="text-xs font-bold text-slate-900 mt-0.5">
                          ₹{Number((sig as any).two_tier_targets.t2_runner.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <div className="text-[10px] text-blue-700 font-semibold">
                          {(sig as any).two_tier_targets.t2_runner.percentage} (Trail SL)
                        </div>
                      </div>
                    </div>
                  ) : (
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
                  )}

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
                        Audit Details <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
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
