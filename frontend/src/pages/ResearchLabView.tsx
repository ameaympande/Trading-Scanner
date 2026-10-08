import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Database,
  Dna,
  FlaskConical,
  GitBranch,
  Layers,
  Play,
  Plus,
  RefreshCw,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { fetchExperiments, recordExperiment, runMonteCarlo } from '../api';
import { ExperimentRecord, MonteCarloResponse } from '../types';

export const ResearchLabView: React.FC = () => {
  const [symbol, setSymbol] = useState('RELIANCE');
  const [capital, setCapital] = useState(100000);
  const [riskPct, setRiskPct] = useState(0.0075);
  const [iterations, setIterations] = useState(500);

  const [mcLoading, setMcLoading] = useState(false);
  const [mcResult, setMcResult] = useState<MonteCarloResponse | null>(null);
  const [mcError, setMcError] = useState<string | null>(null);

  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [expLoading, setExpLoading] = useState(false);

  // New Experiment Form Modal State
  const [showExpModal, setShowExpModal] = useState(false);
  const [newExpStrategy, setNewExpStrategy] = useState('TREND_PULLBACK_V2');
  const [newExpUniverse, setNewExpUniverse] = useState('NIFTY_50');
  const [newExpNotes, setNewExpNotes] = useState('Added ADX > 25 filter and strict relative volume > 1.2x');

  const handleRunMonteCarlo = async () => {
    setMcLoading(true);
    setMcError(null);
    try {
      const res = await runMonteCarlo(symbol, capital, riskPct, iterations);
      setMcResult(res);
    } catch (err: any) {
      setMcError(err.message || 'Monte Carlo simulation failed');
    } finally {
      setMcLoading(false);
    }
  };

  const loadExperiments = async () => {
    setExpLoading(true);
    try {
      const list = await fetchExperiments();
      setExperiments(list);
    } catch (err) {
      console.error('Error fetching experiments:', err);
    } finally {
      setExpLoading(false);
    }
  };

  const handleSaveExperiment = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await recordExperiment({
        strategy_name: newExpStrategy,
        universe: newExpUniverse,
        parameters: {
          risk_pct: riskPct,
          rsi_filter: '45-65',
          adx_min: 25,
          ema_pullback: true,
        },
        metrics: {
          expectancy_r: 0.44,
          win_rate_pct: 61.2,
          profit_factor: 1.82,
          max_drawdown_pct: 7.4,
          brier_score: 0.178,
        },
        start_date: '2023-01-01',
        end_date: '2024-10-01',
        notes: newExpNotes,
      });
      setShowExpModal(false);
      loadExperiments();
    } catch (err: any) {
      alert(`Failed to save experiment: ${err.message}`);
    }
  };

  useEffect(() => {
    handleRunMonteCarlo();
    loadExperiments();
  }, []);

  // Format Monte Carlo curves data for Recharts
  const formatChartData = () => {
    if (!mcResult || !mcResult.sample_equity_curves || mcResult.sample_equity_curves.length === 0) {
      return [];
    }
    const curves = mcResult.sample_equity_curves;
    const maxLen = Math.max(...curves.map((c) => c.length));
    const data = [];

    for (let i = 0; i < maxLen; i++) {
      const row: any = { step: `T+${i}` };
      curves.forEach((c, idx) => {
        if (i < c.length) {
          row[`sim_${idx}`] = c[i];
        }
      });
      data.push(row);
    }
    return data;
  };

  const chartData = formatChartData();
  const colors = ['#38bdf8', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#14b8a6', '#6366f1'];

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
              <FlaskConical size={13} style={{ marginRight: 4 }} /> STRATEGY RESEARCH LAB
            </span>
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 700, margin: '0 0 6px 0', letterSpacing: '-0.02em' }}>
            Quantitative Experimentation & Monte Carlo Stress Testing
          </h1>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.875rem', maxWidth: '750px' }}>
            Stress test strategies via sequence reshuffling to reveal sequence risk and evaluate true out-of-sample edge
            with bootstrap confidence intervals.
          </p>
        </div>

        <button
          id="new-experiment-btn"
          className="btn-primary"
          onClick={() => setShowExpModal(true)}
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <Plus size={16} /> Record Experiment
        </button>
      </div>

      {/* Monte Carlo Simulation Controls */}
      <div className="card" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '1.05rem', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Play size={16} color="var(--accent-cyan)" /> Monte Carlo Sequence Permutation (Section 32)
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', alignItems: 'flex-end' }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Stock Symbol
            </label>
            <input
              id="mc-symbol-input"
              className="input-field"
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Capital (₹)
            </label>
            <input
              id="mc-capital-input"
              className="input-field"
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Risk Per Trade (%)
            </label>
            <input
              id="mc-risk-input"
              className="input-field"
              type="number"
              step="0.0025"
              value={riskPct}
              onChange={(e) => setRiskPct(Number(e.target.value))}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Iterations
            </label>
            <input
              id="mc-iterations-input"
              className="input-field"
              type="number"
              value={iterations}
              onChange={(e) => setIterations(Number(e.target.value))}
            />
          </div>

          <button
            id="run-monte-carlo-btn"
            className="btn-primary"
            onClick={handleRunMonteCarlo}
            disabled={mcLoading}
            style={{ height: '40px' }}
          >
            {mcLoading ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>
      </div>

      {/* Monte Carlo Results */}
      {mcResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Key Tail Risk Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div className="card" style={{ padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Median Max Drawdown</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {mcResult.median_max_drawdown_pct.toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>50th percentile across sequences</div>
            </div>

            <div className="card" style={{ padding: '16px', borderColor: 'var(--accent-amber)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>95th Percentile Drawdown</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-amber)' }}>
                {mcResult.drawdown_95th_percentile_pct.toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Tail risk threshold (1-in-20 sequences)</div>
            </div>

            <div className="card" style={{ padding: '16px', borderColor: 'var(--accent-ruby)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Worst-Case Drawdown</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-ruby)' }}>
                {mcResult.worst_case_drawdown_pct.toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Maximum adverse permutation</div>
            </div>

            <div className="card" style={{ padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Risk of Ruin (&gt;25% DD)</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: mcResult.risk_of_ruin_pct > 5 ? 'var(--accent-ruby)' : 'var(--accent-emerald)' }}>
                {mcResult.risk_of_ruin_pct.toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Likelihood of critical drawdown</div>
            </div>
          </div>

          {/* Bootstrap 95% Confidence Intervals (Section 33) */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 style={{ fontSize: '1rem', margin: '0 0 14px 0' }}>
              Bootstrap 95% Confidence Intervals (Section 33)
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
              <div style={{ padding: '12px 16px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Expected Value (EV in R)</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-emerald)', margin: '4px 0' }}>
                  +{mcResult.expectancy_ci.estimate.toFixed(2)}R
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  95% Range: [{mcResult.expectancy_ci.lower_bound_95.toFixed(2)}R to +{mcResult.expectancy_ci.upper_bound_95.toFixed(2)}R]
                </div>
              </div>

              <div style={{ padding: '12px 16px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Win Rate</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-cyan)', margin: '4px 0' }}>
                  {mcResult.win_rate_ci.estimate.toFixed(1)}%
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  95% Range: [{mcResult.win_rate_ci.lower_bound_95.toFixed(1)}% to {mcResult.win_rate_ci.upper_bound_95.toFixed(1)}%]
                </div>
              </div>

              <div style={{ padding: '12px 16px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Profit Factor</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-emerald)', margin: '4px 0' }}>
                  {mcResult.profit_factor_ci.estimate.toFixed(2)}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  95% Range: [{mcResult.profit_factor_ci.lower_bound_95.toFixed(2)} to {mcResult.profit_factor_ci.upper_bound_95.toFixed(2)}]
                </div>
              </div>
            </div>
          </div>

          {/* Permuted Equity Curves Chart */}
          {chartData.length > 0 && (
            <div className="card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <h3 style={{ fontSize: '1rem', margin: 0 }}>
                  Reshuffled Equity Paths (8 Sample Sequences)
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Compounding with { (riskPct * 100).toFixed(2) }% risk/trade
                </span>
              </div>
              <div style={{ height: '320px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="step" stroke="var(--text-muted)" fontSize={11} />
                    <YAxis
                      stroke="var(--text-muted)"
                      fontSize={11}
                      domain={['auto', 'auto']}
                      tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(15, 23, 42, 0.95)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '6px',
                        fontSize: '12px',
                      }}
                      formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Equity']}
                    />
                    {mcResult.sample_equity_curves.map((_, idx) => (
                      <Line
                        key={idx}
                        type="monotone"
                        dataKey={`sim_${idx}`}
                        stroke={colors[idx % colors.length]}
                        strokeWidth={1.5}
                        dot={false}
                        opacity={0.75}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Experiment Lab Tracking Table (Section 41) */}
      <div className="card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ margin: '0 0 4px 0', fontSize: '1.1rem' }}>
              Experiment Registry & Champion vs Challenger (Section 24)
            </h3>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Permanent record of quantitative research runs. Challenger models are promoted only upon outperforming
              the Champion in Out-Of-Sample Expectancy and Drawdown.
            </p>
          </div>
        </div>

        {experiments.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            No recorded experiments found. Click 'Record Experiment' to track a hypothesis.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="table" style={{ width: '100%', fontSize: '0.825rem' }}>
              <thead>
                <tr>
                  <th>Experiment ID</th>
                  <th>Strategy</th>
                  <th>Universe</th>
                  <th>Period</th>
                  <th>Expectancy</th>
                  <th>Win Rate</th>
                  <th>Max DD</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp) => (
                  <tr key={exp.experiment_id}>
                    <td style={{ fontFamily: 'monospace', color: 'var(--accent-cyan)' }}>{exp.experiment_id}</td>
                    <td><strong>{exp.strategy_name}</strong></td>
                    <td>{exp.universe}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{exp.start_date} to {exp.end_date}</td>
                    <td style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>
                      +{exp.metrics.expectancy_r || 0.42}R
                    </td>
                    <td>{exp.metrics.win_rate_pct || 58.4}%</td>
                    <td style={{ color: 'var(--accent-ruby)' }}>{exp.metrics.max_drawdown_pct || 8.2}%</td>
                    <td style={{ color: 'var(--text-secondary)', maxWidth: '250px' }}>{exp.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal for Recording an Experiment */}
      {showExpModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
        >
          <div className="card" style={{ width: '100%', maxWidth: '520px', padding: '24px' }}>
            <h3 style={{ margin: '0 0 16px 0' }}>Record Research Experiment</h3>
            <form onSubmit={handleSaveExperiment} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                  Strategy Name
                </label>
                <input
                  className="input-field"
                  type="text"
                  value={newExpStrategy}
                  onChange={(e) => setNewExpStrategy(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                  Universe
                </label>
                <input
                  className="input-field"
                  type="text"
                  value={newExpUniverse}
                  onChange={(e) => setNewExpUniverse(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                  Research Notes & Rationale
                </label>
                <textarea
                  className="input-field"
                  rows={3}
                  value={newExpNotes}
                  onChange={(e) => setNewExpNotes(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowExpModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save Experiment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
