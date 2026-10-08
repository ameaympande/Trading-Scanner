import React from 'react';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Compass,
  DollarSign,
  PieChart,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { CandidateSetup, MarketRegime, PaperPortfolio } from '../types';

interface DashboardViewProps {
  regime: MarketRegime | null;
  setups: CandidateSetup[];
  paperPortfolio: PaperPortfolio | null;
  onSelectStock: (symbol: string) => void;
  onNavigateTab: (tab: string) => void;
  onSimulateTrade: (setup: CandidateSetup) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  regime,
  setups,
  paperPortfolio,
  onSelectStock,
  onNavigateTab,
  onSimulateTrade,
}) => {
  const isBull = regime?.regime === 'BULLISH';
  const isBear = regime?.regime === 'BEARISH';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Disclaimer Banner */}
      <div
        style={{
          background: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          fontSize: '0.825rem',
          color: '#fef3c7',
        }}
      >
        <ShieldAlert size={18} color="var(--accent-amber)" style={{ flexShrink: 0 }} />
        <div>
          <strong>Quantitative Research Engine:</strong> Setups reflect defined technical pullback criteria and
          <strong> do not guarantee profit</strong>. Historical backtests contain market slippage and fee friction. Always manage capital according to predefined risk rules.
        </div>
      </div>

      {/* Top Metric Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '16px',
        }}
      >
        {/* Market Regime Card */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
              MARKET REGIME
            </span>
            <span
              className={`badge ${
                isBull ? 'badge-bullish' : isBear ? 'badge-bearish' : 'badge-neutral'
              }`}
            >
              {regime?.regime || 'EVALUATING'}
            </span>
          </div>
          <div style={{ marginTop: '12px', fontSize: '1.6rem', fontWeight: 700, fontFamily: 'var(--font-heading)' }}>
            NIFTY 50: ₹{regime?.close_price.toLocaleString('en-IN') || '—'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Bias Score: {regime ? (regime.score > 0 ? `+${regime.score.toFixed(2)}` : regime.score.toFixed(2)) : '0.00'} (-1.0 to +1.0)
          </div>
          <div style={{ marginTop: '14px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
            <ul style={{ listStyle: 'none', fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {regime?.reasons.slice(0, 2).map((r, i) => (
                <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle2 size={12} color="var(--accent-cyan)" /> {r}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Setups Count */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
              QUALITY SWING SETUPS
            </span>
            <span className="badge badge-cyan">{setups.length} CANDIDATES</span>
          </div>
          <div style={{ marginTop: '12px', fontSize: '1.6rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--accent-cyan)' }}>
            {setups.length > 0 ? `#1: ${setups[0].symbol}` : 'Scanning...'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Avg Score: {setups.length ? Math.round(setups.reduce((a, b) => a + b.score, 0) / setups.length) : 0}/100 | Strategy: TREND_PULLBACK_V1
          </div>
          <div style={{ marginTop: '14px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Min R:R Constraint:</span>
            <span style={{ fontWeight: 600, color: 'var(--accent-emerald)' }}>1:2.0 Minimum</span>
          </div>
        </div>

        {/* Paper Account Value */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
              PAPER TRADING EQUITY
            </span>
            <span className="badge badge-cyan">SIMULATED</span>
          </div>
          <div style={{ marginTop: '12px', fontSize: '1.6rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--accent-emerald)' }}>
            ₹{paperPortfolio?.current_equity.toLocaleString('en-IN') || '1,00,000'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Open Positions: {paperPortfolio?.open_positions.length || 0} | Return: {paperPortfolio?.total_return_pct || 0}%
          </div>
          <div style={{ marginTop: '14px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Simulated Win Rate:</span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{paperPortfolio?.win_rate_pct || 0}%</span>
          </div>
        </div>

        {/* 9-to-5 Workflow Guide */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
              EVENING WORKFLOW
            </span>
            <Clock size={16} color="var(--accent-cyan)" />
          </div>
          <div style={{ marginTop: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Designed for busy 9-to-5 professionals:
          </div>
          <div style={{ marginTop: '10px', fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
            1. Scan runs automatically after 3:30 PM NSE close.<br />
            2. Review top setups & entry zones in the evening.<br />
            3. Set Limit orders before 9:00 AM market open.
          </div>
        </div>
      </div>

      {/* Featured Setups Breakdown */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', fontWeight: 700 }}>
              Top Ranked Swing Opportunities
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Scored from 0–100 matching strict pullback structure, volume confirmation, and risk:reward rules.
            </p>
          </div>
          <button
            className="btn-secondary"
            onClick={() => onNavigateTab('scanner')}
            style={{ fontSize: '0.8rem' }}
          >
            View All in Scanner <ArrowRight size={14} />
          </button>
        </div>

        {setups.length === 0 ? (
          <div
            className="glass-panel"
            style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}
          >
            <Compass size={36} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
            <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              No active signals in this session
            </div>
            <div style={{ fontSize: '0.825rem', marginTop: '6px' }}>
              The quantitative filter is selective. Try scanning with a broader universe (NIFTY 100 / NIFTY 200) or check market regime.
            </div>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
              gap: '20px',
            }}
          >
            {setups.slice(0, 3).map((setup, idx) => (
              <div
                key={setup.symbol}
                className="glass-card"
                style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}
              >
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span
                        style={{
                          fontSize: '1.25rem',
                          fontWeight: 700,
                          fontFamily: 'var(--font-heading)',
                          color: '#fff',
                          cursor: 'pointer',
                        }}
                        onClick={() => onSelectStock(setup.symbol)}
                      >
                        {setup.symbol}
                      </span>
                      <span className="badge badge-cyan">{setup.sector}</span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {setup.company_name}
                    </div>
                  </div>
                  <div
                    style={{
                      textAlign: 'right',
                      background: 'rgba(16, 185, 129, 0.1)',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-md)',
                    }}
                  >
                    <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)', fontWeight: 600 }}>SCORE</div>
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                      {setup.score}/100
                    </div>
                  </div>
                </div>

                {/* Levels Grid */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    background: 'rgba(0, 0, 0, 0.25)',
                    padding: '12px',
                    borderRadius: 'var(--radius-md)',
                    gap: '8px',
                    fontSize: '0.8rem',
                  }}
                >
                  <div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>ENTRY ZONE</div>
                    <div className="num-mono" style={{ fontWeight: 600 }}>
                      ₹{setup.entry_low.toFixed(0)} - ₹{setup.entry_high.toFixed(0)}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: 'var(--accent-ruby)', fontSize: '0.7rem' }}>STOP LOSS</div>
                    <div className="num-mono" style={{ fontWeight: 600, color: 'var(--accent-ruby)' }}>
                      ₹{setup.stop_loss.toFixed(0)}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: 'var(--accent-emerald)', fontSize: '0.7rem' }}>TARGET 1 (R:R)</div>
                    <div className="num-mono" style={{ fontWeight: 600, color: 'var(--accent-emerald)' }}>
                      ₹{setup.target1.toFixed(0)} (1:{setup.risk_reward.toFixed(1)})
                    </div>
                  </div>
                </div>

                {/* Reasons List */}
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    WHY IT TRIGGERED:
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {setup.reasons.slice(0, 3).map((r, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        <CheckCircle2 size={12} color="var(--accent-emerald)" /> {r}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Invalidation */}
                <div
                  style={{
                    background: 'rgba(244, 63, 94, 0.08)',
                    borderLeft: '3px solid var(--accent-ruby)',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.725rem',
                    color: '#fecdd3',
                  }}
                >
                  <span style={{ fontWeight: 600 }}>Invalidation:</span> {setup.invalidation}
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '10px', marginTop: 'auto', paddingTop: '8px' }}>
                  <button
                    className="btn-secondary"
                    style={{ flex: 1, fontSize: '0.775rem' }}
                    onClick={() => onSelectStock(setup.symbol)}
                  >
                    View Chart
                  </button>
                  <button
                    className="btn-success"
                    style={{ flex: 1, fontSize: '0.775rem' }}
                    onClick={() => onSimulateTrade(setup)}
                  >
                    Simulate Paper Trade
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
