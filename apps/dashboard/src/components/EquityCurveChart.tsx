import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import type { TradeSimulation } from '../data/benchmarkData';
import { TrendingUp } from 'lucide-react';

interface EquityCurveChartProps {
  trades: TradeSimulation[];
  startingCapital: number;
}

export const EquityCurveChart: React.FC<EquityCurveChartProps> = ({ trades, startingCapital }) => {
  const chartData = [
    { name: 'Start', equity: startingCapital, pnl: 0, date: 'T-0' },
    ...trades.map((t, idx) => ({
      name: `${t.symbol} (#${idx + 1})`,
      equity: startingCapital + t.cumulative_portfolio_pnl_inr,
      pnl: t.cumulative_portfolio_pnl_inr,
      date: t.date
    }))
  ];

  const lastPnl = trades.length > 0 ? trades[trades.length - 1].cumulative_portfolio_pnl_inr : 0;
  const roiPct = ((lastPnl / startingCapital) * 100).toFixed(2);

  return (
    <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div>
          <h3 className="text-xs font-semibold text-slate-900 flex items-center gap-2">
            <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
            Portfolio Equity Growth Curve (₹{startingCapital.toLocaleString('en-IN')} Capital)
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Portfolio net trajectory after all trading friction and slippage deductions.
          </p>
        </div>

        <div className="text-left sm:text-right">
          <div className="text-[10px] text-slate-400 font-mono uppercase tracking-wider">Cumulative Gain</div>
          <div className="text-sm font-bold text-emerald-600 font-mono">
            +{lastPnl > 0 ? `₹${lastPnl.toLocaleString('en-IN')}` : `₹${lastPnl}`} (+{roiPct}%)
          </div>
        </div>
      </div>

      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#16a34a" stopOpacity={0.20} />
                <stop offset="95%" stopColor="#16a34a" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="name"
              stroke="#94a3b8"
              fontSize={10}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              domain={['auto', 'auto']}
              tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                borderColor: '#e2e8f0',
                borderRadius: '0.5rem',
                fontSize: '11px',
                color: '#0f172a',
                fontFamily: 'monospace',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
              }}
              formatter={(value: any) => [`₹${Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`, 'Equity']}
            />
            <Area
              type="monotone"
              dataKey="equity"
              stroke="#16a34a"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#pnlGrad)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
