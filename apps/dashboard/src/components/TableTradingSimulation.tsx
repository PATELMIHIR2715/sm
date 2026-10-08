import React from 'react';
import type { TradeSimulation } from '../data/benchmarkData';
import { DollarSign, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface TableTradingSimulationProps {
  trades: TradeSimulation[];
  capital: number;
}

export const TableTradingSimulation: React.FC<TableTradingSimulationProps> = ({ trades, capital }) => {
  return (
    <div className="bg-white rounded-xl overflow-hidden border border-slate-200 shadow-xs">
      <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <DollarSign className="w-3.5 h-3.5 text-blue-600" />
            Table 3: Trading Simulation Execution Desk (₹{capital.toLocaleString('en-IN')} Capital)
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Includes 0.30% entry slippage and 0.18% exchange/STT regulatory friction. ₹15,000 baseline trade allocation.
          </p>
        </div>
        <span className="text-[11px] font-mono text-slate-600 bg-slate-50 px-2.5 py-0.5 rounded-md border border-slate-200 self-start sm:self-auto font-semibold">
          {trades.length} Trades Executed
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-800">
          <thead className="bg-slate-50 text-slate-500 uppercase font-mono text-[10px] tracking-wider border-b border-slate-200">
            <tr>
              <th className="py-2.5 px-3">Date & Time</th>
              <th className="py-2.5 px-3">Stock & Action</th>
              <th className="py-2.5 px-3">Invested / Qty</th>
              <th className="py-2.5 px-3">Entry / Exit</th>
              <th className="py-2.5 px-3">Friction</th>
              <th className="py-2.5 px-3">Net Realized P&L</th>
              <th className="py-2.5 px-3">Cumulative Equity</th>
              <th className="py-2.5 px-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono">
            {trades.map((tr) => {
              const isWin = tr.trade_status === 'WIN';
              return (
                <tr key={tr.id} className="hover:bg-slate-50/80 transition">
                  <td className="py-3 px-3 whitespace-nowrap">
                    <div className="font-bold text-slate-900">{tr.date}</div>
                    <div className="text-[10px] text-slate-400">{tr.time}</div>
                  </td>

                  <td className="py-3 px-3 whitespace-nowrap">
                    <div className="font-bold text-slate-900 font-sans">{tr.symbol}</div>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold ${
                        tr.trade_action.includes('BUY')
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-red-50 text-red-700 border border-red-200'
                      }`}
                    >
                      {tr.trade_action}
                    </span>
                  </td>

                  <td className="py-3 px-3 whitespace-nowrap">
                    <div className="text-slate-900 font-medium">₹{tr.invested_capital_inr.toLocaleString('en-IN')}</div>
                    <div className="text-[10px] text-slate-400">{tr.shares_qty} Shares</div>
                  </td>

                  <td className="py-3 px-3 whitespace-nowrap">
                    <div className="text-slate-700">In: ₹{tr.entry_price.toFixed(2)}</div>
                    <div className="text-slate-700">Out: ₹{tr.exit_price.toFixed(2)}</div>
                  </td>

                  <td className="py-3 px-3 text-slate-400 text-[11px] whitespace-nowrap">
                    ₹{tr.friction_charges_inr.toFixed(2)}
                  </td>

                  <td className="py-3 px-3 whitespace-nowrap">
                    <div className={`font-bold flex items-center gap-0.5 ${isWin ? 'text-emerald-600' : 'text-red-600'}`}>
                      {isWin ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                      {isWin ? '+' : ''}₹{tr.net_pnl_inr.toLocaleString('en-IN')}
                    </div>
                    <div className={`text-[10px] font-semibold ${isWin ? 'text-emerald-700' : 'text-red-600'}`}>
                      {tr.net_return_pct > 0 ? '+' : ''}{tr.net_return_pct.toFixed(2)}%
                    </div>
                  </td>

                  <td className="py-3 px-3 whitespace-nowrap">
                    <div className="font-bold text-slate-900">
                      ₹{(capital + tr.cumulative_portfolio_pnl_inr).toLocaleString('en-IN')}
                    </div>
                  </td>

                  <td className="py-3 px-3 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        isWin
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-red-50 text-red-700 border border-red-200'
                      }`}
                    >
                      {tr.trade_status}
                    </span>
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
