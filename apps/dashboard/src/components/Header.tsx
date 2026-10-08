import { Activity, RefreshCw, Layers } from 'lucide-react';

interface HeaderProps {
  currentTimelineKey: string;
  onTimelineChange: (key: string) => void;
  isRefreshing: boolean;
  onRefresh: () => void;
  onOpenNotifications?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTimelineKey,
  onTimelineChange,
  isRefreshing,
  onRefresh,
  onOpenNotifications
}) => {
  return (
    <header className="border-b border-slate-200 bg-white/95 sticky top-0 z-50 backdrop-blur-md shadow-xs">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-2.5 sm:py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 sm:gap-4">
        {/* Brand & System Status */}
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 shrink-0">
            <Activity className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center space-x-2">
              <h1 className="text-sm sm:text-base font-bold tracking-tight text-slate-900 truncate">
                NIFTY 500 AI News Engine
              </h1>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
                LIVE
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-mono hidden sm:block">
              Institutional Zero-Lookahead NLP &bull; Multi-Channel Alerts &bull; ₹1,00,000 Portfolio
            </p>
          </div>
        </div>

        {/* Timeline Selector, Notifications & Refresh */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-0.5 sm:pb-0 w-full sm:w-auto justify-between sm:justify-end">

          {onOpenNotifications && (
            <button
              onClick={onOpenNotifications}
              className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-mono font-semibold bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 transition shadow-2xs relative group shrink-0 cursor-pointer"
            >
              <span className="relative flex h-2 w-2 mr-0.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="hidden xs:inline">Alerts</span>
              <span className="xs:hidden">Alerts</span>
              <span className="px-1.5 py-0.2 text-[9px] rounded-md bg-purple-100 text-purple-700 font-bold border border-purple-200">
                Jev AI
              </span>
            </button>
          )}

          <div className="flex items-center bg-slate-50 rounded-lg border border-slate-200 px-2 sm:px-2.5 py-1 shrink-0">
            <Layers className="w-3.5 h-3.5 text-blue-600 mr-1.5 shrink-0" />
            <select
              value={currentTimelineKey}
              onChange={(e) => onTimelineChange(e.target.value)}
              className="bg-transparent text-xs text-slate-800 font-mono focus:outline-none cursor-pointer pr-1 max-w-[150px] sm:max-w-none truncate"
            >
              <option value="sep2026_live" className="bg-white text-slate-900">
                Live Cycle (Sep 18 – 28, 2026)
              </option>
              <option value="blind_10day" className="bg-white text-slate-900">
                Blind 10-Day (May 06 – 17, 2024)
              </option>
              <option value="blind_20day" className="bg-white text-slate-900">
                Blind 20-Day (Jul 08 – Aug 02, 2024)
              </option>
              <option value="blind_30day" className="bg-white text-slate-900">
                Blind 30-Day (Jan 02 – Feb 12, 2024)
              </option>
            </select>
          </div>

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white transition disabled:opacity-50 shadow-xs shrink-0 cursor-pointer"
          >
            <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">{isRefreshing ? 'Syncing...' : 'Sync Feed'}</span>
            <span className="sm:hidden">{isRefreshing ? '...' : 'Sync'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
