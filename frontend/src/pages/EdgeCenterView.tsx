import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Cpu,
  Layers,
  LineChart,
  RefreshCw,
  Scale,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { fetchEdgeCenter } from '../api';
import { EdgeCenterResponse } from '../types';

export const EdgeCenterView: React.FC = () => {
  const [data, setData] = useState<EdgeCenterResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchEdgeCenter();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch Edge Center');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-muted)' }}>
        <RefreshCw className="pulse-glow" size={32} style={{ margin: '0 auto 16px' }} />
        <p>Loading Quantitative Edge Center & Regime Telemetry...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="card" style={{ padding: '24px', borderColor: 'var(--accent-ruby)', textAlign: 'center' }}>
        <AlertTriangle color="var(--accent-ruby)" size={32} style={{ margin: '0 auto 12px' }} />
        <h3>Edge Center Telemetry Unavailable</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '16px' }}>{error}</p>
        <button className="btn-primary" onClick={loadData}>Retry</button>
      </div>
    );
  }

  const { regime, drawdown_protection, champion_model, edge_decay, drift_status, top_failure_reasons } = data;

  const isBull = regime.state.includes('BULL');
  const isBear = regime.state.includes('BEAR');
  const ddMode = drawdown_protection.mode;

  const ddColor =
    ddMode === 'NORMAL'
      ? 'var(--accent-emerald)'
      : ddMode === 'CAUTION'
      ? 'var(--accent-amber)'
      : 'var(--accent-ruby)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div
        className="card"
        style={{
          padding: '24px',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.7))',
          borderColor: 'rgba(56, 189, 248, 0.25)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span className="badge badge-bullish" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', borderColor: 'rgba(56, 189, 248, 0.3)' }}>
              <BrainCircuit size={13} style={{ marginRight: 4 }} /> QUANTITATIVE EDGE CENTER
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Updated: {new Date(data.timestamp).toLocaleTimeString()}
            </span>
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 700, margin: '0 0 6px 0', letterSpacing: '-0.02em' }}>
            Adaptive System Telemetry & Risk Throttling
          </h1>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.875rem', maxWidth: '750px' }}>
            Continuous learning engine monitoring market regime states, calibrated probability distributions,
            feature drift, edge decay, and portfolio drawdown protection.
          </p>
        </div>

        <button
          id="refresh-edge-center-btn"
          className="btn-secondary"
          onClick={loadData}
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <RefreshCw size={15} /> Refresh Telemetry
        </button>
      </div>

      {/* Grid of Key Pillars */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {/* Card 1: Market Regime */}
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Broad Market Regime
            </span>
            <Activity size={18} color={isBull ? 'var(--accent-emerald)' : isBear ? 'var(--accent-ruby)' : 'var(--accent-amber)'} />
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: isBull ? 'var(--accent-emerald)' : isBear ? 'var(--accent-ruby)' : 'var(--accent-amber)', marginBottom: '8px' }}>
            {regime.state}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
            NIFTY: ₹{regime.benchmark_close.toLocaleString()} ({regime.nifty_20d_return >= 0 ? '+' : ''}{regime.nifty_20d_return.toFixed(2)}% 20D) | RSI: {regime.rsi14.toFixed(1)}
          </div>
          <div style={{ padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px', fontSize: '0.75rem', color: 'var(--text-primary)' }}>
            <strong>Directive:</strong> {regime.recommendation}
          </div>
        </div>

        {/* Card 2: Drawdown Protection State */}
        <div className="card" style={{ padding: '20px', borderColor: ddColor }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Drawdown Protection State
            </span>
            <ShieldAlert size={18} color={ddColor} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '8px' }}>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: ddColor }}>
              {drawdown_protection.mode}
            </div>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              ({drawdown_protection.drawdown_pct.toFixed(2)}% Drawdown)
            </span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
            Allowed Positions: <strong>{drawdown_protection.max_positions}</strong> | Risk Scaling: <strong>{(drawdown_protection.risk_multiplier * 100).toFixed(0)}%</strong>
          </div>
          <div style={{ padding: '8px 12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '6px', fontSize: '0.75rem', color: 'var(--text-primary)' }}>
            {drawdown_protection.message}
          </div>
        </div>

        {/* Card 3: Model Calibration */}
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Champion ML Model
            </span>
            <Cpu size={18} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
            {champion_model.model_id}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
            {champion_model.algorithm} • Platt Scaling
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.75rem' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 8px', borderRadius: '4px' }}>
              <div style={{ color: 'var(--text-muted)' }}>Brier Score</div>
              <div style={{ fontWeight: 600, color: 'var(--accent-emerald)' }}>{champion_model.brier_score} (Calibrated)</div>
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '6px 8px', borderRadius: '4px' }}>
              <div style={{ color: 'var(--text-muted)' }}>Expected Value</div>
              <div style={{ fontWeight: 600, color: 'var(--accent-emerald)' }}>+{champion_model.expected_value_r.toFixed(2)}R</div>
            </div>
          </div>
        </div>

        {/* Card 4: Edge Decay & Drift */}
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Edge Decay & Drift Monitor
            </span>
            <Zap size={18} color={edge_decay.is_decay_detected ? 'var(--accent-ruby)' : 'var(--accent-emerald)'} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '8px' }}>
            <div style={{ fontSize: '1.3rem', fontWeight: 700, color: edge_decay.is_decay_detected ? 'var(--accent-ruby)' : 'var(--accent-emerald)' }}>
              {edge_decay.is_decay_detected ? 'DECAY DETECTED' : 'EDGE ACTIVE'}
            </div>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
            Recent 20 EV: <strong>+{edge_decay.expectancy_recent_r.toFixed(2)}R</strong> (Baseline: +{edge_decay.baseline_expectancy_r.toFixed(2)}R)
          </div>
          <div style={{ padding: '6px 10px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Feature Drift: <strong style={{ color: drift_status.is_drift_detected ? 'var(--accent-ruby)' : 'var(--accent-emerald)' }}>
              {drift_status.is_drift_detected ? 'Detected' : 'Stable (KS p>0.05)'}
            </strong>
          </div>
        </div>
      </div>

      {/* Main Analysis Section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
        {/* Left Column: Failure Taxonomy & Root Causes */}
        <div className="card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <AlertOctagon size={20} color="var(--accent-ruby)" />
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Loss Diagnosis & Failure Taxonomy (Section 21)</h3>
          </div>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Every stopped trade is categorized into structural failure modes. The system learns which market conditions
            cause false breakouts and automatically downweights vulnerable setups.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {top_failure_reasons.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '12px 14px',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                    {item.reason}
                  </span>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-ruby)' }}>
                    {item.pct}% of Losses
                  </span>
                </div>
                <div style={{ width: '100%', height: '5px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden', marginBottom: '8px' }}>
                  <div style={{ width: `${item.pct}%`, height: '100%', background: 'var(--accent-ruby)' }} />
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <strong style={{ color: 'var(--accent-cyan)' }}>Rule Adjustment:</strong> {item.solution}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Setup Quality Criteria (Section 29) */}
        <div className="card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <Scale size={20} color="var(--accent-emerald)" />
            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Setup Quality Grading Rubric (A+ to REJECT)</h3>
          </div>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Setups are graded not by arbitrary score, but by combining Base Strategy Score + Calibrated P(+2R) +
            Empirical Expectancy + Relative Strength + Sample Size Confidence.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ padding: '10px 14px', background: 'rgba(16, 185, 129, 0.06)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span className="badge badge-bullish" style={{ fontWeight: 700 }}>GRADE A+ (Highest Quality)</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Full Size Allowed</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Meta Score ≥ 82 • Calibrated P(+2R) ≥ 56% • Cond. EV ≥ +0.30R • Outperforming NIFTY (RS &gt; 1.02x)
              </div>
            </div>

            <div style={{ padding: '10px 14px', background: 'rgba(56, 189, 248, 0.06)', border: '1px solid rgba(56, 189, 248, 0.25)', borderRadius: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', fontWeight: 700 }}>GRADE A (Standard Swing)</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>85% Sizing</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Meta Score ≥ 74 • Calibrated P(+2R) ≥ 50% • Cond. EV ≥ +0.15R • Clean technical qualification
              </div>
            </div>

            <div style={{ padding: '10px 14px', background: 'rgba(245, 158, 11, 0.06)', border: '1px solid rgba(245, 158, 11, 0.25)', borderRadius: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span className="badge badge-neutral" style={{ fontWeight: 700 }}>GRADE B (Marginal Edge)</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>60% Sizing</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Meta Score ≥ 66 • Calibrated P(+2R) ≥ 45% • Cond. EV ≥ 0.0R • Requires tight stop placement
              </div>
            </div>

            <div style={{ padding: '10px 14px', background: 'rgba(239, 68, 68, 0.06)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span className="badge badge-bearish" style={{ fontWeight: 700 }}>GRADE C / REJECT (No Trade)</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>0% Sizing (Filtered Out)</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Meta Score &lt; 66 or negative conditional expectancy or weak market regime. Execution prohibited.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
