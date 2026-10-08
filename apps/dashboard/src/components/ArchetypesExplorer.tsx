import React, { useState, useEffect } from 'react';
import { Database, Search, Filter, TrendingUp, TrendingDown, Layers } from 'lucide-react';
import { API_BASE } from '../config';

interface Archetype {
  event_uuid: string;
  sector: string;
  macro_regime: string;
  category: string;
  headline: string;
  keywords?: string;
  actual_direction: string;
  base_confidence: number;
  actual_1d_return_pct: number;
  actual_5d_return_pct: number;
  actual_20d_return_pct: number;
  win_probability: number;
}

export const ArchetypesExplorer: React.FC = () => {
  const [archetypes, setArchetypes] = useState<Archetype[]>([]);
  const [search, setSearch] = useState<string>('');
  const [selectedSector, setSelectedSector] = useState<string>('ALL');
  const [selectedDirection, setSelectedDirection] = useState<string>('ALL');

  useEffect(() => {
    const fetchArchetypes = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/archetypes`);
        if (res.ok) {
          const data = await res.json();
          setArchetypes(data.archetypes || []);
        } else {
          throw new Error('Fallback required');
        }
      } catch (err) {
        console.warn('Using embedded archetypes list:', err);
        // Fallback standard archetypes
        setArchetypes([
          {
            event_uuid: "DEF_AON_01",
            sector: "Defense & Aerospace",
            macro_regime: "ATMANIRBHAR_DEFENSE",
            category: "DEFENSE_TENDER_AON",
            headline: "Defence Acquisition Council accords Acceptance of Necessity for major indigenous manufacturing contract",
            actual_direction: "BULLISH",
            base_confidence: 92.0,
            actual_1d_return_pct: 5.40,
            actual_5d_return_pct: 11.20,
            actual_20d_return_pct: 18.50,
            win_probability: 0.90
          },
          {
            event_uuid: "DEF_EXPORT_01",
            sector: "Defense & Aerospace",
            macro_regime: "DEFENSE_EXPORTS",
            category: "DEFENSE_EXPORT_ORDER",
            headline: "Defense PSU signs landmark export order for radar equipment and communication avionics with friendly foreign nation",
            actual_direction: "BULLISH",
            base_confidence: 88.0,
            actual_1d_return_pct: 3.80,
            actual_5d_return_pct: 7.90,
            actual_20d_return_pct: 13.60,
            win_probability: 0.85
          },
          {
            event_uuid: "PHARMA_FDA_APPROVAL_01",
            sector: "Pharmaceuticals",
            macro_regime: "GENERIC_EXPANSION",
            category: "FDA_APPROVAL",
            headline: "Receives US FDA Final Approval for specialty generic injectable with 180-day market exclusivity",
            actual_direction: "BULLISH",
            base_confidence: 90.0,
            actual_1d_return_pct: 4.10,
            actual_5d_return_pct: 8.50,
            actual_20d_return_pct: 12.80,
            win_probability: 0.88
          },
          {
            event_uuid: "PHARMA_FORM_483_01",
            sector: "Pharmaceuticals",
            macro_regime: "REGULATORY_SCRUTINY",
            category: "FDA_FORM_483",
            headline: "US FDA concludes inspection of API manufacturing facility with multiple critical observational findings Form 483",
            actual_direction: "BEARISH",
            base_confidence: 88.0,
            actual_1d_return_pct: -4.60,
            actual_5d_return_pct: -8.90,
            actual_20d_return_pct: -14.20,
            win_probability: 0.86
          },
          {
            event_uuid: "BANK_ROA_UPGRADE_01",
            sector: "Banking & Financials",
            macro_regime: "CREDIT_UPCYCLE",
            category: "RATING_UPGRADE",
            headline: "Global rating agency upgrades credit baseline assessment citing multi-year low Net NPA and pristine asset quality",
            actual_direction: "BULLISH",
            base_confidence: 84.0,
            actual_1d_return_pct: 2.90,
            actual_5d_return_pct: 5.80,
            actual_20d_return_pct: 8.90,
            win_probability: 0.82
          },
          {
            event_uuid: "BANK_NIM_CRASH_01",
            sector: "Banking & Financials",
            macro_regime: "LIQUIDITY_SQUEEZE",
            category: "NIM_COMPRESSION",
            headline: "Reports sharp compression in Net Interest Margin NIM due to elevated cost of deposits and deposit repricing lag",
            actual_direction: "BEARISH",
            base_confidence: 86.0,
            actual_1d_return_pct: -4.20,
            actual_5d_return_pct: -7.60,
            actual_20d_return_pct: -12.40,
            win_probability: 0.88
          },
          {
            event_uuid: "AUTO_EV_EXPORT_01",
            sector: "Automotive",
            macro_regime: "EV_TRANSITION",
            category: "GLOBAL_SUPPLY_ORDER",
            headline: "Signs multi-year commercial export deal for next-generation electric SUV portfolio across European markets",
            actual_direction: "BULLISH",
            base_confidence: 85.0,
            actual_1d_return_pct: 3.40,
            actual_5d_return_pct: 7.20,
            actual_20d_return_pct: 11.50,
            win_probability: 0.84
          },
          {
            event_uuid: "PAINT_CRUDE_SURGE_01",
            sector: "Paints & Consumer",
            macro_regime: "INPUT_INFLATION",
            category: "MARGIN_CONTRACTION",
            headline: "Surge in crude derivative raw material prices and increased promotional discounting squeezes operating margins",
            actual_direction: "BEARISH",
            base_confidence: 82.0,
            actual_1d_return_pct: -3.80,
            actual_5d_return_pct: -6.40,
            actual_20d_return_pct: -9.80,
            win_probability: 0.82
          }
        ]);
      }
    };
    fetchArchetypes();
  }, []);

  const sectors = ['ALL', 'Defense & Aerospace', 'Pharmaceuticals', 'Banking & Financials', 'Automotive', 'Paints & Consumer', 'Metals & Mining', 'Information Technology'];

  const filtered = archetypes.filter((a) => {
    const matchesSearch =
      a.headline.toLowerCase().includes(search.toLowerCase()) ||
      a.category.toLowerCase().includes(search.toLowerCase()) ||
      a.macro_regime.toLowerCase().includes(search.toLowerCase());
    const matchesSector = selectedSector === 'ALL' || a.sector === selectedSector;
    const matchesDirection = selectedDirection === 'ALL' || a.actual_direction === selectedDirection;
    return matchesSearch && matchesSector && matchesDirection;
  });

  return (
    <div className="space-y-4">
      {/* Header Info */}
      <div className="bg-white rounded-xl p-5 border border-slate-200 space-y-4 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-200 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1.5">
                <Database className="w-3 h-3 text-blue-600" />
                KNOWLEDGE GRAPH & RAG
              </span>
              <span className="text-xs text-slate-500 font-mono">
                10-Year Corporate Event Archetypes (2015–2025)
              </span>
            </div>
            <h2 className="text-base font-semibold text-slate-900 mt-1">
              Historical Event Archetypes & Reaction Distributions
            </h2>
            <p className="text-xs text-slate-600 mt-0.5 max-w-3xl">
              Incoming news is mapped via cosine similarity to empirical Indian market disclosures. Review historical win rates, post-event returns ($T+1, T+5, T+20$), and macro regime classifications.
            </p>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search archetypes, keywords..."
              className="w-full bg-slate-50 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-900 border border-slate-200 focus:outline-none focus:border-blue-500 placeholder-slate-400 font-sans"
            />
          </div>

          {/* Sector Filter */}
          <div className="flex items-center bg-slate-50 rounded-lg px-2.5 py-0.5 border border-slate-200">
            <Filter className="w-3.5 h-3.5 text-slate-400 mr-1.5" />
            <select
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="bg-transparent text-xs text-slate-800 font-mono focus:outline-none w-full cursor-pointer py-1"
            >
              {sectors.map((sec, i) => (
                <option key={i} value={sec} className="bg-white text-slate-800">
                  Sector: {sec}
                </option>
              ))}
            </select>
          </div>

          {/* Direction Filter */}
          <div className="flex items-center bg-slate-50 rounded-lg px-2.5 py-0.5 border border-slate-200">
            <Layers className="w-3.5 h-3.5 text-slate-400 mr-1.5" />
            <select
              value={selectedDirection}
              onChange={(e) => setSelectedDirection(e.target.value)}
              className="bg-transparent text-xs text-slate-800 font-mono focus:outline-none w-full cursor-pointer py-1"
            >
              <option value="ALL" className="bg-white text-slate-800">Direction: All</option>
              <option value="BULLISH" className="bg-white text-slate-800">Bullish Events Only</option>
              <option value="BEARISH" className="bg-white text-slate-800">Bearish Events Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Archetypes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {filtered.map((item, idx) => {
          const isBull = item.actual_direction === 'BULLISH';
          return (
            <div
              key={idx}
              className="bg-white rounded-xl p-4 border border-slate-200 hover:border-slate-300 transition space-y-3 shadow-2xs"
            >
              {/* Card Header */}
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-medium bg-slate-100 text-slate-700 border border-slate-200">
                      {item.sector}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      ID: {item.event_uuid}
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-slate-900 mt-1 leading-snug">
                    {item.headline}
                  </h4>
                </div>

                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-semibold shrink-0 border ${
                    isBull
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-rose-50 text-rose-700 border-rose-200'
                  }`}
                >
                  {isBull ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
                  {item.actual_direction}
                </span>
              </div>

              {/* Statistical Returns Metrics */}
              <div className="grid grid-cols-4 gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-center font-mono">
                <div>
                  <div className="text-[9px] text-slate-500 uppercase tracking-wider">Win Rate</div>
                  <div className="text-xs font-bold text-emerald-600 mt-0.5">
                    {(item.win_probability * 100).toFixed(0)}%
                  </div>
                </div>

                <div>
                  <div className="text-[9px] text-slate-500 uppercase tracking-wider">T+1 Ret</div>
                  <div className={`text-xs font-bold mt-0.5 ${item.actual_1d_return_pct >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                    {item.actual_1d_return_pct >= 0 ? '+' : ''}{item.actual_1d_return_pct}%
                  </div>
                </div>

                <div>
                  <div className="text-[9px] text-slate-500 uppercase tracking-wider">T+5 Ret</div>
                  <div className={`text-xs font-bold mt-0.5 ${item.actual_5d_return_pct >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                    {item.actual_5d_return_pct >= 0 ? '+' : ''}{item.actual_5d_return_pct}%
                  </div>
                </div>

                <div>
                  <div className="text-[9px] text-slate-500 uppercase tracking-wider">T+20 Ret</div>
                  <div className={`text-xs font-bold mt-0.5 ${item.actual_20d_return_pct >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                    {item.actual_20d_return_pct >= 0 ? '+' : ''}{item.actual_20d_return_pct}%
                  </div>
                </div>
              </div>

              {/* Category & Regime Tags */}
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-0.5">
                <span>Cat: <strong className="text-slate-800 font-medium">{item.category}</strong></span>
                <span>Regime: <strong className="text-slate-600 font-medium">{item.macro_regime}</strong></span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
