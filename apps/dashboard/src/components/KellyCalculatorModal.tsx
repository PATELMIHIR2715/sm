import React, { useState } from 'react';
import { X, Calculator } from 'lucide-react';

interface KellyCalculatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultSymbol?: string;
  defaultLtp?: number;
}

export const KellyCalculatorModal: React.FC<KellyCalculatorModalProps> = ({
  isOpen,
  onClose,
  defaultSymbol = 'HAL',
  defaultLtp = 4738.0,
}) => {
  const [portfolioCapital, setPortfolioCapital] = useState<number>(100000);
  const [ltp, setLtp] = useState<number>(defaultLtp);
  const [winProbPct, setWinProbPct] = useState<number>(85);
  const [targetGainPct, setTargetGainPct] = useState<number>(5.4);
  const [stopLossRiskPct, setStopLossRiskPct] = useState<number>(3.2);
  const [kellyFraction, setKellyFraction] = useState<number>(0.5); // 0.5 = Half Kelly

  if (!isOpen) return null;

  // Kelly Math
  const p = Math.max(0.01, Math.min(0.99, winProbPct / 100));
  const q = 1 - p;
  const b = Math.max(0.1, targetGainPct / stopLossRiskPct); // Payoff ratio

  // Full Kelly = (p*b - q) / b
  const fullKelly = Math.max(0, (p * b - q) / b);
  const targetFraction = Math.min(0.25, Math.max(0.05, fullKelly * kellyFraction));
  const optimalCapital = Math.round(portfolioCapital * targetFraction);
  const sharesQty = Math.max(1, Math.floor(optimalCapital / ltp));
  const actualDeployedCapital = sharesQty * ltp;
  const maxRupeeRisk = Math.round(actualDeployedCapital * (stopLossRiskPct / 100));
  const expectedProfit = Math.round(actualDeployedCapital * (targetGainPct / 100));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-lg w-full p-4 sm:p-6 shadow-2xl space-y-4 my-auto">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-3.5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center">
              <Calculator className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Kelly Position Sizer ({defaultSymbol})
              </h3>
              <p className="text-[11px] text-slate-500 font-mono">
                Volatility-Adjusted Fractional Allocation Desk
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-800 border border-slate-200 transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Inputs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div>
            <label className="text-slate-600 block mb-1 font-semibold">Portfolio Capital (₹):</label>
            <input
              type="number"
              value={portfolioCapital}
              onChange={(e) => setPortfolioCapital(Number(e.target.value))}
              className="w-full bg-slate-50 px-3 py-1.5 rounded-lg text-slate-900 font-bold border border-slate-200 focus:outline-none focus:border-blue-600"
            />
          </div>

          <div>
            <label className="text-slate-600 block mb-1 font-semibold">Stock LTP (₹):</label>
            <input
              type="number"
              value={ltp}
              onChange={(e) => setLtp(Number(e.target.value))}
              className="w-full bg-slate-50 px-3 py-1.5 rounded-lg text-slate-900 font-bold border border-slate-200 focus:outline-none focus:border-blue-600"
            />
          </div>

          <div>
            <label className="text-slate-600 block mb-1 font-semibold">Target Gain Expected (%):</label>
            <input
              type="number"
              step="0.1"
              value={targetGainPct}
              onChange={(e) => setTargetGainPct(Number(e.target.value))}
              className="w-full bg-slate-50 px-3 py-1.5 rounded-lg text-emerald-700 font-bold border border-slate-200 focus:outline-none focus:border-blue-600"
            />
          </div>

          <div>
            <label className="text-slate-600 block mb-1 font-semibold">Stop Loss Risk (%):</label>
            <input
              type="number"
              step="0.1"
              value={stopLossRiskPct}
              onChange={(e) => setStopLossRiskPct(Number(e.target.value))}
              className="w-full bg-slate-50 px-3 py-1.5 rounded-lg text-red-600 font-bold border border-slate-200 focus:outline-none focus:border-blue-600"
            />
          </div>

          <div>
            <label className="text-slate-600 block mb-1 font-semibold">Win Prob (%):</label>
            <input
              type="number"
              value={winProbPct}
              onChange={(e) => setWinProbPct(Number(e.target.value))}
              className="w-full bg-slate-50 px-3 py-1.5 rounded-lg text-slate-900 font-bold border border-slate-200 focus:outline-none focus:border-blue-600"
            />
          </div>

          <div>
            <label className="text-slate-600 block mb-1 font-semibold">Payoff Ratio (b = Gain/Loss):</label>
            <div className="w-full bg-slate-50 px-3 py-1.5 rounded-lg text-slate-800 font-bold border border-slate-200 flex items-center justify-between">
              <span>{b.toFixed(2)} : 1</span>
              <span className="text-[10px] text-slate-500 font-normal">
                (+{targetGainPct}% / -{stopLossRiskPct}%)
              </span>
            </div>
          </div>
        </div>

        {/* Kelly Multiplier Fraction Toggle */}
        <div>
          <label className="text-[11px] font-mono text-slate-600 block mb-1 font-semibold">
            Risk Conservatism Fraction:
          </label>
          <div className="grid grid-cols-3 gap-2 text-xs font-mono font-medium">
            <button
              onClick={() => setKellyFraction(0.25)}
              className={`py-1.5 rounded-lg border transition cursor-pointer font-bold ${
                kellyFraction === 0.25
                  ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
            >
              0.25x Quarter
            </button>
            <button
              onClick={() => setKellyFraction(0.5)}
              className={`py-1.5 rounded-lg border transition cursor-pointer font-bold ${
                kellyFraction === 0.5
                  ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
            >
              0.50x Half (Std)
            </button>
            <button
              onClick={() => setKellyFraction(1.0)}
              className={`py-1.5 rounded-lg border transition cursor-pointer font-bold ${
                kellyFraction === 1.0
                  ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
              }`}
            >
              1.00x Full
            </button>
          </div>
        </div>

        {/* Results Card */}
        <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 space-y-2.5 font-mono">
          <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
            <span className="text-xs text-slate-500 font-semibold">Optimal Allocation:</span>
            <span className="text-sm font-bold text-emerald-700">
              {(targetFraction * 100).toFixed(1)}% of Capital
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <div className="text-slate-500 text-[10px]">Capital:</div>
              <div className="text-xs font-bold text-slate-900 mt-0.5">
                ₹{actualDeployedCapital.toLocaleString('en-IN')}
              </div>
            </div>

            <div>
              <div className="text-slate-500 text-[10px]">Quantity:</div>
              <div className="text-xs font-bold text-slate-700 mt-0.5">
                {sharesQty} Shares
              </div>
            </div>

            <div>
              <div className="text-slate-500 text-[10px]">Target Profit (+{targetGainPct}%):</div>
              <div className="text-xs font-bold text-emerald-700 mt-0.5">
                +₹{expectedProfit.toLocaleString('en-IN')}
              </div>
            </div>

            <div>
              <div className="text-slate-500 text-[10px]">Stop-Loss Risk (-{stopLossRiskPct}%):</div>
              <div className="text-xs font-bold text-red-600 mt-0.5">
                -₹{maxRupeeRisk.toLocaleString('en-IN')}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 pt-1">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg text-xs font-mono font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
