import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  DollarSign,
  Filter,
  Info,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Wallet,
  X,
  Zap,
} from 'lucide-react';
import { CandidateSetup } from '../types';

interface ScannerViewProps {
  setups: CandidateSetup[];
  onSelectStock: (symbol: string) => void;
  onSimulateTrade: (setup: CandidateSetup) => void;
  capital: number;
  setCapital: (val: number) => void;
  riskPct: number;
  setRiskPct: (val: number) => void;
  selectedUniverse: string;
  setSelectedUniverse: (u: string) => void;
  onTriggerScan: (universeOverride?: string) => void;
  isScanning: boolean;
}

export const ScannerView: React.FC<ScannerViewProps> = ({
  setups,
  onSelectStock,
  onSimulateTrade,
  capital,
  setCapital,
  riskPct,
  setRiskPct,
  selectedUniverse,
  setSelectedUniverse,
  onTriggerScan,
  isScanning,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [minScore, setMinScore] = useState(70);
  const [minRR, setMinRR] = useState(2.0);
  const [gradeFilter, setGradeFilter] = useState<'ALL' | 'A+' | 'A' | 'B'>('ALL');
  const [onlyWithinBudget, setOnlyWithinBudget] = useState(capital <= 10000);
  const [selectedSetup, setSelectedSetup] = useState<CandidateSetup | null>(null);

  // Capital presets including micro-budget option (1000, 5000) for testing
  const fundPresets = [1000, 5000, 25000, 50000, 100000, 500000];

  // Helper to compute grade
  const getSetupGrade = (s: CandidateSetup): string => {
    if (s.setup_grade) return s.setup_grade;
    if (s.score >= 82) return 'A+';
    if (s.score >= 74) return 'A';
    return 'B';
  };

  // Helper to calculate dynamic position sizing strictly respecting user budget
  const getDynamicSizing = (s: CandidateSetup) => {
    const entryPrice = s.entry_low;
    const stopPrice = s.stop_loss;
    const riskPerShare = Math.max(0.01, entryPrice - stopPrice);
    const rewardPerShare = Math.max(0.01, s.target1 - entryPrice);

    // Is 1 share affordable with current account capital?
    const isAffordable = capital >= entryPrice;
    const minCapitalNeeded = entryPrice;
    const deficit = Math.max(0, entryPrice - capital);

    // Dynamic Sizing Budget
    // For small capital (<= ₹25,000), allow single position allocation up to 100% of budget
    // For larger capital, cap single position at 20%
    const maxPosRatio = capital <= 25000 ? 1.0 : 0.20;
    const maxPosBudget = capital * maxPosRatio;
    const maxRiskBudget = capital * riskPct;

    let dynamicQty = 0;
    if (isAffordable) {
      const qtyByRisk = Math.floor(maxRiskBudget / riskPerShare);
      const qtyByCap = Math.floor(maxPosBudget / Math.max(1, entryPrice));
      // If affordable, allow at least 1 share
      dynamicQty = Math.max(1, Math.min(qtyByRisk, qtyByCap));
      // Strictly cannot exceed total account capital
      const maxAffordableQty = Math.floor(capital / entryPrice);
      dynamicQty = Math.min(dynamicQty, maxAffordableQty);
    }

    const moneyTaken = dynamicQty * entryPrice;
    const riskTaken = dynamicQty * riskPerShare;
    const rewardExpected = dynamicQty * rewardPerShare;
    const fundPctTaken = capital > 0 ? (moneyTaken / capital) * 100 : 0;
    const riskPctTaken = capital > 0 ? (riskTaken / capital) * 100 : 0;

    return {
      isAffordable,
      minCapitalNeeded,
      deficit,
      quantity: dynamicQty,
      moneyTaken,
      riskTaken,
      rewardExpected,
      fundPctTaken,
      riskPctTaken,
      riskPerShare,
      rewardPerShare,
    };
  };

  // Grade Counts
  const gradeCounts = {
    ALL: setups.length,
    'A+': setups.filter((s) => getSetupGrade(s) === 'A+').length,
    A: setups.filter((s) => getSetupGrade(s) === 'A' || getSetupGrade(s) === 'A+').length,
    B: setups.filter((s) => ['A+', 'A', 'B'].includes(getSetupGrade(s))).length,
  };

  // Affordable counts
  const affordableCount = setups.filter((s) => s.entry_low <= capital).length;

  // Filtered setups with affordable setups prioritized at the top
  const filtered = setups
    .filter((s) => {
      const sGrade = getSetupGrade(s);
      const matchGrade =
        gradeFilter === 'ALL'
          ? true
          : gradeFilter === 'A+'
          ? sGrade === 'A+'
          : gradeFilter === 'A'
          ? sGrade === 'A+' || sGrade === 'A'
          : true;

      const matchBudget = onlyWithinBudget ? s.entry_low <= capital : true;

      const matchSearch =
        s.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.sector.toLowerCase().includes(searchTerm.toLowerCase());
      const matchScore = s.score >= minScore;
      const matchRR = s.risk_reward >= minRR;
      return matchGrade && matchBudget && matchSearch && matchScore && matchRR;
    })
    .sort((a, b) => {
      const aAff = a.entry_low <= capital ? 0 : 1;
      const bAff = b.entry_low <= capital ? 0 : 1;
      if (aAff !== bAff) return aAff - bAff;
      return b.score - a.score;
    });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Dynamic Fund Allocation & Risk Profile Panel */}
      <div
        className="card"
        style={{
          padding: '20px',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.75))',
          borderColor: 'rgba(56, 189, 248, 0.3)',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '8px',
                background: 'rgba(56, 189, 248, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-cyan)',
              }}
            >
              <Wallet size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>
                Dynamic Capital Budget & Risk Profile
              </h2>
              <p style={{ margin: 0, fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                Set your budget (e.g. ₹1,000, ₹50,000) to see exact affordable trades, money taken, and risk per setup.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              className="badge"
              style={{
                fontSize: '0.75rem',
                padding: '4px 10px',
                background: affordableCount > 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                color: affordableCount > 0 ? 'var(--accent-emerald)' : 'var(--accent-ruby)',
                borderColor: affordableCount > 0 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)',
              }}
            >
              {affordableCount > 0 ? (
                <>
                  <CheckCircle2 size={13} style={{ marginRight: 4 }} /> {affordableCount} Trade{affordableCount > 1 ? 's' : ''} Fit Budget
                </>
              ) : (
                <>
                  <AlertCircle size={13} style={{ marginRight: 4 }} /> 0 Trades Fit ₹{capital.toLocaleString('en-IN')} Budget
                </>
              )}
            </span>
          </div>
        </div>

        {/* Dynamic Fund Inputs & Quick Presets */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
          {/* Fund Presets */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Quick Budget Presets
            </span>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {fundPresets.map((amt) => {
                const isSelected = capital === amt;
                return (
                  <button
                    key={amt}
                    onClick={() => {
                      setCapital(amt);
                      if (amt <= 10000) setOnlyWithinBudget(true);
                    }}
                    style={{
                      padding: '6px 12px',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.8rem',
                      fontWeight: isSelected ? 700 : 500,
                      background: isSelected ? 'rgba(56, 189, 248, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                      color: isSelected ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                      border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    ₹{amt >= 100000 ? `${amt / 100000}L` : amt >= 1000 ? `${amt / 1000}k` : amt}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Numeric Capital Input */}
          <div style={{ display: 'flex', gap: '14px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div>
              <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px', fontWeight: 600 }}>
                YOUR BUDGET / CAPITAL (₹)
              </label>
              <input
                id="scanner-dynamic-capital"
                type="number"
                value={capital}
                onChange={(e) => {
                  const val = Math.max(100, Number(e.target.value));
                  setCapital(val);
                  if (val <= 10000) setOnlyWithinBudget(true);
                }}
                style={{
                  background: 'var(--bg-surface-elevated)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-subtle)',
                  padding: '7px 12px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  width: '120px',
                  fontFamily: 'var(--font-mono)',
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px', fontWeight: 600 }}>
                RISK / TRADE (%)
              </label>
              <select
                value={riskPct}
                onChange={(e) => setRiskPct(Number(e.target.value))}
                style={{
                  background: 'var(--bg-surface-elevated)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-subtle)',
                  padding: '7px 12px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  fontFamily: 'var(--font-mono)',
                  outline: 'none',
                }}
              >
                <option value={0.005}>0.50% Risk</option>
                <option value={0.0075}>0.75% Risk (Standard)</option>
                <option value={0.01}>1.00% Risk</option>
                <option value={0.015}>1.50% Risk</option>
                <option value={0.02}>2.00% Risk</option>
              </select>
            </div>

            {/* Fund Telemetry Chips */}
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '16px' }}>
              <div style={{ padding: '6px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px', border: '1px solid var(--border-subtle)', fontSize: '0.75rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Max Risk Allowance: </span>
                <strong style={{ color: 'var(--accent-ruby)' }}>
                  ₹{Math.max(1, capital * riskPct).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </strong>
              </div>
              <div style={{ padding: '6px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px', border: '1px solid var(--border-subtle)', fontSize: '0.75rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Max Trade Budget: </span>
                <strong style={{ color: 'var(--accent-emerald)' }}>
                  ₹{(capital <= 25000 ? capital : capital * 0.20).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </strong>
              </div>
            </div>
          </div>
        </div>

        {/* Budget Match & Universe Guidance Banner */}
        {setups.length > 0 && affordableCount > 0 ? (
          <div
            style={{
              padding: '12px 18px',
              background: 'linear-gradient(90deg, rgba(16, 185, 129, 0.12), rgba(6, 78, 59, 0.08))',
              border: '1px solid rgba(16, 185, 129, 0.35)',
              borderRadius: '8px',
              fontSize: '0.85rem',
              color: '#d1fae5',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CheckCircle2 size={18} color="var(--accent-emerald)" style={{ flexShrink: 0 }} />
              <div>
                <strong>Budget Match (₹{capital.toLocaleString('en-IN')}):</strong> Found <strong>{affordableCount} swing setup{affordableCount > 1 ? 's' : ''}</strong> that fit into your ₹{capital.toLocaleString('en-IN')} capital!
                {filtered.filter((s) => s.entry_low <= capital).length > 0 && (
                  <span style={{ marginLeft: 8, color: '#a7f3d0' }}>
                    Top pick: <strong>{filtered.filter((s) => s.entry_low <= capital)[0].symbol}</strong> @ ₹{filtered.filter((s) => s.entry_low <= capital)[0].entry_low.toFixed(1)}/sh (Grade {getSetupGrade(filtered.filter((s) => s.entry_low <= capital)[0])}).
                  </span>
                )}
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-bullish" style={{ fontSize: '0.75rem', padding: '4px 10px' }}>
                {affordableCount} Affordable Setup{affordableCount > 1 ? 's' : ''}
              </span>
            </div>
          </div>
        ) : setups.length > 0 && affordableCount === 0 ? (
          <div
            style={{
              padding: '12px 18px',
              background: 'linear-gradient(90deg, rgba(56, 189, 248, 0.1), rgba(15, 23, 42, 0.6))',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              borderRadius: '8px',
              fontSize: '0.85rem',
              color: '#e0f2fe',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Info size={18} color="var(--accent-cyan)" style={{ flexShrink: 0 }} />
              <div>
                <strong>Active Budget: ₹{capital.toLocaleString('en-IN')}:</strong> In {selectedUniverse.replace('_', ' ')}, setups trade above ₹{capital.toLocaleString('en-IN')} (e.g. {setups[0]?.symbol} at ₹{setups[0]?.entry_low.toLocaleString('en-IN', { maximumFractionDigits: 0 })}). Click below to scan <strong>NIFTY 200</strong> for setups like <strong>PETRONET (₹288)</strong> and <strong>BHEL (₹429)</strong> that fit your ₹{capital.toLocaleString('en-IN')} budget!
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn-primary"
                style={{ fontSize: '0.775rem', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
                onClick={() => {
                  setSelectedUniverse('NIFTY_200');
                  onTriggerScan('NIFTY_200');
                }}
              >
                <Search size={14} /> Scan NIFTY 200 for Trades Under ₹{capital.toLocaleString('en-IN')}
              </button>
            </div>
          </div>
        ) : null}
      </div>

      {/* 2. "Scan For" Controls & Filters */}
      <div
        className="glass-panel"
        style={{
          padding: '18px 20px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '16px',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center' }}>
          {/* Universe selector */}
          <div>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px', fontWeight: 600 }}>
              SCAN UNIVERSE
            </label>
            <select
              id="scanner-universe-select"
              value={selectedUniverse}
              onChange={(e) => setSelectedUniverse(e.target.value)}
              style={{
                background: 'var(--bg-surface-elevated)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.85rem',
                outline: 'none',
                fontWeight: 600,
              }}
            >
              <option value="NIFTY_50">NIFTY 50 (Bluechips)</option>
              <option value="NIFTY_NEXT_50">NIFTY Next 50 (Growth)</option>
              <option value="NIFTY_100">NIFTY 100 (Large Cap)</option>
              <option value="NIFTY_200">NIFTY 200 (Broad Market)</option>
            </select>
          </div>

          {/* Grade Filter Tabs */}
          <div>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px', fontWeight: 600 }}>
              FILTER BY SETUP GRADE
            </label>
            <div style={{ display: 'flex', gap: '6px' }}>
              {(['ALL', 'A+', 'A', 'B'] as const).map((grade) => {
                const isActive = gradeFilter === grade;
                const count = gradeCounts[grade];
                return (
                  <button
                    key={grade}
                    onClick={() => setGradeFilter(grade)}
                    style={{
                      padding: '7px 12px',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.775rem',
                      fontWeight: isActive ? 700 : 500,
                      background: isActive ? 'rgba(56, 189, 248, 0.18)' : 'rgba(255, 255, 255, 0.03)',
                      color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                      border: isActive ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                    }}
                  >
                    {grade === 'A+' && <Sparkles size={12} color="#10b981" />}
                    <span>{grade === 'ALL' ? 'All Grades' : `Grade ${grade}`}</span>
                    <span
                      style={{
                        background: 'rgba(255, 255, 255, 0.1)',
                        padding: '1px 5px',
                        borderRadius: '10px',
                        fontSize: '0.7rem',
                      }}
                    >
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Budget Filter Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px' }}>
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '0.8rem',
                color: onlyWithinBudget ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                fontWeight: onlyWithinBudget ? 600 : 400,
                cursor: 'pointer',
                background: onlyWithinBudget ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                padding: '6px 10px',
                borderRadius: '6px',
                border: onlyWithinBudget ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid transparent',
              }}
            >
              <input
                type="checkbox"
                checked={onlyWithinBudget}
                onChange={(e) => setOnlyWithinBudget(e.target.checked)}
                style={{ accentColor: 'var(--accent-cyan)' }}
              />
              Fit Within ₹{capital.toLocaleString('en-IN')} Budget Only
            </label>
          </div>

          {/* Search box */}
          <div>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px', fontWeight: 600 }}>
              SEARCH SYMBOL / SECTOR
            </label>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
                padding: '7px 12px',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <Search size={14} color="var(--text-muted)" />
              <input
                id="scanner-search-input"
                type="text"
                placeholder="e.g. RELIANCE, Pharma..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem',
                  outline: 'none',
                  width: '160px',
                }}
              />
            </div>
          </div>
        </div>

        {/* Scan Action Button */}
        <div>
          <button
            id="scanner-scan-now-btn"
            className="btn-primary"
            onClick={() => onTriggerScan()}
            disabled={isScanning}
            style={{ padding: '9px 18px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <RefreshCw size={15} className={isScanning ? 'pulse-glow' : ''} />
            {isScanning ? 'Scanning Universe...' : 'Scan for Setups'}
          </button>
        </div>
      </div>

      {/* 3. Main Candidates Table with Money Taken, Profile & Risk */}
      <div className="glass-panel" style={{ overflowX: 'auto' }}>
        <table className="data-table" style={{ width: '100%' }}>
          <thead>
            <tr>
              <th style={{ width: '45px', textAlign: 'center' }}>Rank</th>
              <th style={{ textAlign: 'center', width: '70px' }}>Grade</th>
              <th>Symbol & Company</th>
              <th>Sector</th>
              <th style={{ textAlign: 'center' }}>Score</th>
              <th style={{ textAlign: 'right' }}>LTP (₹)</th>
              <th style={{ textAlign: 'right' }}>Entry Zone (₹)</th>
              <th style={{ textAlign: 'right', color: 'var(--accent-ruby)' }}>Stop Loss (₹)</th>
              <th style={{ textAlign: 'right', color: 'var(--accent-emerald)' }}>Target 1 (₹)</th>
              <th style={{ textAlign: 'center' }}>R:R</th>
              <th style={{ textAlign: 'center' }}>Budget Status</th>
              <th style={{ textAlign: 'right', color: 'var(--accent-cyan)' }}>Dynamic Qty</th>
              <th style={{ textAlign: 'right', color: '#f8fafc' }}>Money Taken (₹)</th>
              <th style={{ textAlign: 'right', color: 'var(--accent-amber)' }}>Risk Taken (₹)</th>
              <th style={{ textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={15} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  {onlyWithinBudget ? (
                    <div style={{ maxWidth: '520px', margin: '0 auto', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                      <AlertCircle size={32} color="var(--accent-amber)" />
                      <h4 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-primary)' }}>
                        No Setups Under ₹{capital.toLocaleString('en-IN')} in {selectedUniverse.replace('_', ' ')}
                      </h4>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                        {selectedUniverse === 'NIFTY_50'
                          ? `NIFTY 50 bluechips trade above your ₹${capital.toLocaleString('en-IN')} budget.`
                          : `Setups in this universe currently exceed ₹${capital.toLocaleString('en-IN')}.`}{' '}
                        Broader universes like <strong>NIFTY 200</strong> contain setups like <strong>PETRONET (₹288.50)</strong> and <strong>BHEL (₹429.60)</strong> that fit within ₹{capital.toLocaleString('en-IN')}.
                      </p>
                      <button
                        className="btn-primary"
                        style={{ padding: '8px 18px', fontSize: '0.825rem', display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px' }}
                        onClick={() => {
                          setSelectedUniverse('NIFTY_200');
                          onTriggerScan('NIFTY_200');
                        }}
                      >
                        <Search size={15} /> Scan NIFTY 200 for Trades Under ₹{capital.toLocaleString('en-IN')}
                      </button>
                    </div>
                  ) : (
                    'No candidates match the specified filters. Try lowering the minimum score or expanding the universe.'
                  )}
                </td>
              </tr>
            ) : (
              filtered.map((setup, idx) => {
                const grade = getSetupGrade(setup);
                const sizing = getDynamicSizing(setup);

                return (
                  <tr key={setup.symbol} style={{ opacity: sizing.isAffordable ? 1.0 : 0.85 }}>
                    <td style={{ textAlign: 'center', fontWeight: 600, color: 'var(--text-muted)' }}>
                      {idx + 1}
                    </td>

                    {/* Grade Badge */}
                    <td style={{ textAlign: 'center' }}>
                      <span
                        className={
                          grade === 'A+'
                            ? 'badge badge-bullish'
                            : grade === 'A'
                            ? 'badge'
                            : 'badge badge-neutral'
                        }
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '3px 8px',
                          background:
                            grade === 'A+'
                              ? 'rgba(16, 185, 129, 0.2)'
                              : grade === 'A'
                              ? 'rgba(56, 189, 248, 0.15)'
                              : 'rgba(245, 158, 11, 0.15)',
                        }}
                      >
                        {grade === 'A+' ? '⭐ A+' : grade}
                      </span>
                    </td>

                    {/* Symbol */}
                    <td>
                      <div
                        style={{ fontWeight: 600, color: '#fff', cursor: 'pointer' }}
                        onClick={() => onSelectStock(setup.symbol)}
                      >
                        {setup.symbol}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{setup.company_name}</div>
                    </td>

                    {/* Sector */}
                    <td>
                      <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>
                        {setup.sector || 'Equities'}
                      </span>
                    </td>

                    {/* Score */}
                    <td style={{ textAlign: 'center' }}>
                      <span
                        style={{
                          padding: '3px 8px',
                          borderRadius: 'var(--radius-sm)',
                          fontWeight: 700,
                          fontSize: '0.8rem',
                          background: 'rgba(16, 185, 129, 0.15)',
                          color: 'var(--accent-emerald)',
                        }}
                      >
                        {setup.score}
                      </span>
                    </td>

                    {/* LTP */}
                    <td className="num-mono" style={{ textAlign: 'right', fontWeight: 600 }}>
                      ₹{setup.current_price.toFixed(2)}
                    </td>

                    {/* Entry Zone */}
                    <td className="num-mono" style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>
                      ₹{setup.entry_low.toFixed(2)}–{setup.entry_high.toFixed(2)}
                    </td>

                    {/* Stop Loss */}
                    <td className="num-mono" style={{ textAlign: 'right', color: 'var(--accent-ruby)', fontWeight: 600 }}>
                      ₹{setup.stop_loss.toFixed(2)}
                    </td>

                    {/* Target 1 */}
                    <td className="num-mono" style={{ textAlign: 'right', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                      ₹{setup.target1.toFixed(2)}
                    </td>

                    {/* R:R */}
                    <td style={{ textAlign: 'center', fontWeight: 600 }}>
                      1:{setup.risk_reward.toFixed(1)}
                    </td>

                    {/* Budget Status */}
                    <td style={{ textAlign: 'center' }}>
                      {sizing.isAffordable ? (
                        <span className="badge badge-bullish" style={{ fontSize: '0.7rem' }}>
                          ✓ Fits Budget
                        </span>
                      ) : (
                        <span
                          className="badge badge-bearish"
                          style={{ fontSize: '0.7rem' }}
                          title={`Requires ₹${sizing.minCapitalNeeded.toLocaleString('en-IN')} minimum (deficit ₹${sizing.deficit.toLocaleString('en-IN')})`}
                        >
                          Exceeds (Need ₹{(sizing.minCapitalNeeded / 1000).toFixed(1)}k)
                        </span>
                      )}
                    </td>

                    {/* Dynamic Quantity */}
                    <td className="num-mono" style={{ textAlign: 'right', fontWeight: 700 }}>
                      {sizing.isAffordable ? (
                        <span style={{ color: 'var(--accent-cyan)' }}>
                          {sizing.quantity} <span style={{ fontSize: '0.675rem', color: 'var(--text-muted)' }}>shs</span>
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>0 shs</span>
                      )}
                    </td>

                    {/* Money Taken / Position Value */}
                    <td className="num-mono" style={{ textAlign: 'right', fontWeight: 600 }}>
                      {sizing.isAffordable ? (
                        <div>
                          <div>₹{sizing.moneyTaken.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
                          <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)' }}>
                            ({sizing.fundPctTaken.toFixed(1)}% of fund)
                          </div>
                        </div>
                      ) : (
                        <div style={{ color: 'var(--accent-ruby)', fontSize: '0.75rem' }}>
                          Need ₹{sizing.minCapitalNeeded.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                        </div>
                      )}
                    </td>

                    {/* Risk Taken */}
                    <td className="num-mono" style={{ textAlign: 'right', color: 'var(--accent-amber)', fontWeight: 600 }}>
                      {sizing.isAffordable ? (
                        <div>
                          <div>₹{sizing.riskTaken.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
                          <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)' }}>
                            ({sizing.riskPctTaken.toFixed(2)}% risk)
                          </div>
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>₹0</span>
                      )}
                    </td>

                    {/* Actions */}
                    <td style={{ textAlign: 'center' }}>
                      <div style={{ display: 'flex', gap: '6px', justifyContent: 'center' }}>
                        <button
                          className="btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '0.725rem' }}
                          onClick={() => setSelectedSetup(setup)}
                          title="View Setup Profile & Risk Breakdown"
                        >
                          Profile
                        </button>
                        <button
                          className="btn-success"
                          style={{
                            padding: '4px 8px',
                            fontSize: '0.725rem',
                            opacity: sizing.isAffordable ? 1.0 : 0.4,
                            cursor: sizing.isAffordable ? 'pointer' : 'not-allowed',
                          }}
                          disabled={!sizing.isAffordable}
                          onClick={() => {
                            if (sizing.isAffordable) {
                              onSimulateTrade({
                                ...setup,
                                suggested_qty: sizing.quantity,
                                position_value: sizing.moneyTaken,
                              });
                            }
                          }}
                          title={
                            sizing.isAffordable
                              ? `Simulate Paper Trade with ${sizing.quantity} shares`
                              : `Trade disabled: requires ₹${sizing.minCapitalNeeded.toLocaleString('en-IN')} (exceeds your ₹${capital.toLocaleString('en-IN')} budget)`
                          }
                        >
                          {sizing.isAffordable ? 'Trade' : 'Need Capital'}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* 4. Complete Setup Profile & Risk Modal */}
      {selectedSetup && (() => {
        const grade = getSetupGrade(selectedSetup);
        const sizing = getDynamicSizing(selectedSetup);

        return (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.75)',
              backdropFilter: 'blur(8px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
              padding: '20px',
            }}
            onClick={() => setSelectedSetup(null)}
          >
            <div
              className="card"
              style={{
                width: '100%',
                maxWidth: '650px',
                maxHeight: '90vh',
                overflowY: 'auto',
                padding: '28px',
                display: 'flex',
                flexDirection: 'column',
                gap: '18px',
                border: '1px solid rgba(56, 189, 248, 0.3)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <h3 style={{ fontSize: '1.4rem', fontFamily: 'var(--font-heading)', color: '#fff', margin: 0 }}>
                      {selectedSetup.symbol}
                    </h3>
                    <span className="badge badge-cyan">{selectedSetup.sector}</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px', marginBottom: '8px' }}>
                    {selectedSetup.company_name} — {selectedSetup.strategy_name}
                  </div>

                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <span className="badge badge-bullish" style={{ fontWeight: 700 }}>
                      Grade: {grade === 'A+' ? '⭐ A+' : grade}
                    </span>
                    <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>
                      ML P(+2R before -1R): {selectedSetup.ml_prob_pct || 60}%
                    </span>
                    <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)' }}>
                      Cond. EV: +{(selectedSetup.expected_value_r || 0.35).toFixed(2)}R
                    </span>
                  </div>
                </div>

                <button
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                  onClick={() => setSelectedSetup(null)}
                >
                  <X size={20} />
                </button>
              </div>

              {/* Complete Risk & Profile Section */}
              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.7)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldAlert size={16} color="var(--accent-amber)" /> Trade Profile & Risk Allocation (Budget: ₹{capital.toLocaleString('en-IN')})
                </div>

                {sizing.isAffordable ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px', fontSize: '0.775rem' }}>
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 10px', borderRadius: '4px' }}>
                      <div style={{ color: 'var(--text-muted)' }}>Position Size</div>
                      <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.95rem' }}>{sizing.quantity} shares</div>
                    </div>
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 10px', borderRadius: '4px' }}>
                      <div style={{ color: 'var(--text-muted)' }}>Money Taken</div>
                      <div style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '0.95rem' }}>
                        ₹{sizing.moneyTaken.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                      </div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>{sizing.fundPctTaken.toFixed(1)}% of budget</div>
                    </div>
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 10px', borderRadius: '4px' }}>
                      <div style={{ color: 'var(--text-muted)' }}>Risk at Stop</div>
                      <div style={{ fontWeight: 700, color: 'var(--accent-ruby)', fontSize: '0.95rem' }}>
                        ₹{sizing.riskTaken.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                      </div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>{sizing.riskPctTaken.toFixed(2)}% of account</div>
                    </div>
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 10px', borderRadius: '4px' }}>
                      <div style={{ color: 'var(--text-muted)' }}>Target 1 Reward</div>
                      <div style={{ fontWeight: 700, color: 'var(--accent-emerald)', fontSize: '0.95rem' }}>
                        +₹{sizing.rewardExpected.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                      </div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>1:{selectedSetup.risk_reward.toFixed(1)} R:R</div>
                    </div>
                  </div>
                ) : (
                  <div
                    style={{
                      padding: '12px',
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      color: '#fecdd3',
                    }}
                  >
                    <strong>⚠️ Budget Deficit:</strong> This stock trades at ₹{selectedSetup.entry_low.toLocaleString('en-IN')} per share.
                    Your budget is ₹{capital.toLocaleString('en-IN')}, leaving a deficit of <strong>₹{sizing.deficit.toLocaleString('en-IN')}</strong>.
                    You need at least <strong>₹{sizing.minCapitalNeeded.toLocaleString('en-IN')}</strong> to purchase 1 share of this stock.
                  </div>
                )}
              </div>

              {/* Trade Levels Profile */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', fontSize: '0.8rem' }}>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Entry Zone</div>
                  <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.95rem' }}>
                    ₹{selectedSetup.entry_low.toFixed(2)}–{selectedSetup.entry_high.toFixed(2)}
                  </div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Stop Loss</div>
                  <div style={{ fontWeight: 700, color: 'var(--accent-ruby)', fontSize: '0.95rem' }}>
                    ₹{selectedSetup.stop_loss.toFixed(2)} (-{((selectedSetup.entry_low - selectedSetup.stop_loss) / selectedSetup.entry_low * 100).toFixed(1)}%)
                  </div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Target 1</div>
                  <div style={{ fontWeight: 700, color: 'var(--accent-emerald)', fontSize: '0.95rem' }}>
                    ₹{selectedSetup.target1.toFixed(2)} (+{((selectedSetup.target1 - selectedSetup.entry_low) / selectedSetup.entry_low * 100).toFixed(1)}%)
                  </div>
                </div>
              </div>

              {/* Why It Triggered */}
              <div>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: '8px' }}>
                  Technical Qualification Breakdown:
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {selectedSetup.reasons.map((r, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem' }}>
                      <CheckCircle2 size={14} color="var(--accent-emerald)" />
                      {r}
                    </div>
                  ))}
                </div>
              </div>

              {/* Invalidation */}
              <div
                style={{
                  background: 'rgba(244, 63, 94, 0.1)',
                  borderLeft: '4px solid var(--accent-ruby)',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.8rem',
                  color: '#fecdd3',
                }}
              >
                <strong>Invalidation Rule:</strong> {selectedSetup.invalidation}
              </div>

              {/* Modal Actions */}
              <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
                <button
                  className="btn-secondary"
                  style={{ flex: 1 }}
                  onClick={() => {
                    onSelectStock(selectedSetup.symbol);
                    setSelectedSetup(null);
                  }}
                >
                  View Candlestick Chart
                </button>
                <button
                  className="btn-success"
                  style={{
                    flex: 1,
                    opacity: sizing.isAffordable ? 1.0 : 0.5,
                    cursor: sizing.isAffordable ? 'pointer' : 'not-allowed',
                  }}
                  disabled={!sizing.isAffordable}
                  onClick={() => {
                    if (sizing.isAffordable) {
                      onSimulateTrade({
                        ...selectedSetup,
                        suggested_qty: sizing.quantity,
                        position_value: sizing.moneyTaken,
                      });
                      setSelectedSetup(null);
                    }
                  }}
                >
                  {sizing.isAffordable
                    ? `Execute Dynamic Trade (${sizing.quantity} shs)`
                    : `Cannot Trade (Need ₹${sizing.minCapitalNeeded.toLocaleString('en-IN')})`}
                </button>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};
