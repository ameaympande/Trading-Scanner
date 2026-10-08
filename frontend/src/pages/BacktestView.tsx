import React, { useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Layers,
  Play,
  RotateCcw,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';
import { runBacktest, runWalkForward } from '../api';
import { BacktestResponse, WalkForwardResult } from '../types';

export const BacktestView: React.FC = () => {
  const [symbol, setSymbol] = useState('RELIANCE');
  const [capital, setCapital] = useState(100000);
  const [riskPct, setRiskPct] = useState(0.0075);
  const [loading, setLoading] = useState(false);
  const [backtestResult, setBacktestResult] = useState<BacktestResponse | null>(null);
  const [wfResult, setWfResult] = useState<WalkForwardResult | null>(null);
  const [activeTab, setActiveTab] = useState<'standard' | 'walk-forward'>('standard');
  const [error, setError] = useState<string | null>(null);

  const handleRunBacktest = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runBacktest(symbol, capital, riskPct);
      setBacktestResult(res);

      const wf = await runWalkForward(symbol, capital);
      setWfResult(wf);
    } catch (err: any) {
      setError(err.message || 'Backtest failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Configuration Bar */}
      <div
        className="glass-panel"
        style={{
          padding: '20px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '20px',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center' }}>
          <div>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              STOCK SYMBOL (NSE)
            </label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              style={{
                background: 'var(--bg-surface-elevated)',
                color: '#fff',
                border: '1px solid var(--border-subtle)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.9rem',
                fontWeight: 600,
                width: '130px',
                textTransform: 'uppercase',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              INITIAL CAPITAL (₹)
            </label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              style={{
                background: 'var(--bg-surface-elevated)',
                color: '#fff',
                border: '1px solid var(--border-subtle)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.9rem',
                width: '130px',
                fontFamily: 'var(--font-mono)',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              RISK PER TRADE (%)
            </label>
            <input
              type="number"
              step={0.0025}
              value={riskPct * 100}
              onChange={(e) => setRiskPct(Number(e.target.value) / 100)}
              style={{
                background: 'var(--bg-surface-elevated)',
                color: '#fff',
                border: '1px solid var(--border-subtle)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.9rem',
                width: '90px',
                fontFamily: 'var(--font-mono)',
              }}
            />
          </div>
        </div>

        <button className="btn-primary" onClick={handleRunBacktest} disabled={loading}>
          <Play size={16} />
          {loading ? 'Simulating...' : 'Run Simulation'}
        </button>
      </div>

      {error && (
        <div className="glass-panel" style={{ padding: '20px', color: 'var(--accent-ruby)', textAlign: 'center' }}>
          {error}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          className={activeTab === 'standard' ? 'btn-primary' : 'btn-secondary'}
          style={{ fontSize: '0.825rem' }}
          onClick={() => setActiveTab('standard')}
        >
          Comprehensive Backtest
        </button>
        <button
          className={activeTab === 'walk-forward' ? 'btn-primary' : 'btn-secondary'}
          style={{ fontSize: '0.825rem' }}
          onClick={() => setActiveTab('walk-forward')}
        >
          Walk-Forward Validation (Train vs OOS)
        </button>
      </div>

      {/* Standard Tab View */}
      {activeTab === 'standard' && backtestResult && (
        <>
          {/* Key Metrics Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
            }}
          >
            <div className="glass-panel" style={{ padding: '18px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>TOTAL RETURN</div>
              <div className="num-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: backtestResult.metrics.total_return_pct >= 0 ? 'var(--accent-emerald)' : 'var(--accent-ruby)' }}>
                {backtestResult.metrics.total_return_pct > 0 ? '+' : ''}{backtestResult.metrics.total_return_pct}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                CAGR: {backtestResult.metrics.cagr_pct}%
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '18px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>WIN RATE & TRADES</div>
              <div className="num-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: '#fff' }}>
                {backtestResult.metrics.win_rate_pct}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                {backtestResult.metrics.winning_trades} Wins / {backtestResult.metrics.losing_trades} Losses ({backtestResult.metrics.total_trades} Total)
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '18px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PROFIT FACTOR</div>
              <div className="num-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: '#fff' }}>
                {backtestResult.metrics.profit_factor}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Win/Loss Ratio: {backtestResult.metrics.win_loss_ratio}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '18px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>MAX DRAWDOWN</div>
              <div className="num-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-ruby)' }}>
                -{backtestResult.metrics.max_drawdown_pct}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Sharpe: {backtestResult.metrics.sharpe_ratio} | Sortino: {backtestResult.metrics.sortino_ratio}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '18px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>TRANSACTION FRICTION</div>
              <div className="num-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-amber)' }}>
                ₹{backtestResult.metrics.total_transaction_costs.toLocaleString('en-IN')}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                STT, DP, GST & Slippage Deducted
              </div>
            </div>
          </div>

          {/* Equity Curve Chart */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '16px' }}>
              SIMULATED PORTFOLIO EQUITY CURVE (₹)
            </h3>
            <div style={{ width: '100%', height: '320px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={backtestResult.metrics.equity_curve}>
                  <defs>
                    <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--accent-cyan)" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="var(--accent-cyan)" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} />
                  <YAxis orientation="right" stroke="var(--text-muted)" fontSize={11} domain={['auto', 'auto']} tickFormatter={(v) => `₹${v.toLocaleString('en-IN')}`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(14, 18, 27, 0.95)',
                      borderColor: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '8px',
                      fontSize: '0.75rem',
                    }}
                  />
                  <Area type="monotone" dataKey="equity" stroke="var(--accent-cyan)" fill="url(#equityGrad)" strokeWidth={2} name="Equity (₹)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trade History Log */}
          <div className="glass-panel" style={{ overflow: 'hidden' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', fontWeight: 600, fontSize: '0.9rem' }}>
              Executed Trade Log ({backtestResult.trades.length} Trades)
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Entry Date</th>
                  <th>Exit Date</th>
                  <th style={{ textAlign: 'right' }}>Entry (₹)</th>
                  <th style={{ textAlign: 'right' }}>Exit (₹)</th>
                  <th style={{ textAlign: 'right' }}>Qty</th>
                  <th style={{ textAlign: 'right' }}>Net P&L (₹)</th>
                  <th style={{ textAlign: 'right' }}>P&L %</th>
                  <th>Exit Reason</th>
                  <th style={{ textAlign: 'right' }}>Friction (₹)</th>
                </tr>
              </thead>
              <tbody>
                {backtestResult.trades.length === 0 ? (
                  <tr>
                    <td colSpan={9} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                      No trades triggered during this period.
                    </td>
                  </tr>
                ) : (
                  backtestResult.trades.map((t, idx) => (
                    <tr key={idx}>
                      <td style={{ fontSize: '0.8rem' }}>{t.entry_date}</td>
                      <td style={{ fontSize: '0.8rem' }}>{t.exit_date}</td>
                      <td className="num-mono" style={{ textAlign: 'right' }}>₹{t.entry_price.toFixed(2)}</td>
                      <td className="num-mono" style={{ textAlign: 'right' }}>₹{t.exit_price.toFixed(2)}</td>
                      <td className="num-mono" style={{ textAlign: 'right' }}>{t.quantity}</td>
                      <td className="num-mono" style={{ textAlign: 'right', fontWeight: 600, color: t.net_pnl >= 0 ? 'var(--accent-emerald)' : 'var(--accent-ruby)' }}>
                        {t.net_pnl > 0 ? '+' : ''}₹{t.net_pnl.toFixed(2)}
                      </td>
                      <td className="num-mono" style={{ textAlign: 'right', color: t.net_pnl_pct >= 0 ? 'var(--accent-emerald)' : 'var(--accent-ruby)' }}>
                        {t.net_pnl_pct > 0 ? '+' : ''}{t.net_pnl_pct.toFixed(2)}%
                      </td>
                      <td>
                        <span className={`badge ${t.exit_reason === 'TARGET' ? 'badge-bullish' : t.exit_reason === 'STOP_LOSS' ? 'badge-bearish' : 'badge-neutral'}`}>
                          {t.exit_reason}
                        </span>
                      </td>
                      <td className="num-mono" style={{ textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                        ₹{t.friction_cost.toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Walk Forward Tab View */}
      {activeTab === 'walk-forward' && wfResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Survivorship Warning */}
          <div
            style={{
              background: 'rgba(244, 63, 94, 0.08)',
              border: '1px solid rgba(244, 63, 94, 0.25)',
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              gap: '12px',
              alignItems: 'center',
              fontSize: '0.825rem',
              color: '#fecdd3',
            }}
          >
            <AlertTriangle size={20} color="var(--accent-ruby)" style={{ flexShrink: 0 }} />
            <div>
              <strong>Survivorship & Look-Ahead Bias Notice:</strong> {wfResult.warning}
            </div>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '20px',
            }}
          >
            {/* In-Sample Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                  IN-SAMPLE (TRAIN)
                </span>
                <span className="badge badge-cyan">{wfResult.in_sample.period}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Return:</span>
                  <span className="num-mono" style={{ fontWeight: 700, color: wfResult.in_sample.return_pct >= 0 ? 'var(--accent-emerald)' : 'var(--accent-ruby)' }}>
                    {wfResult.in_sample.return_pct > 0 ? '+' : ''}{wfResult.in_sample.return_pct}%
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Win Rate:</span>
                  <span className="num-mono" style={{ fontWeight: 600 }}>{wfResult.in_sample.win_rate}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Sharpe Ratio:</span>
                  <span className="num-mono" style={{ fontWeight: 600 }}>{wfResult.in_sample.sharpe}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Max Drawdown:</span>
                  <span className="num-mono" style={{ color: 'var(--accent-ruby)' }}>-{wfResult.in_sample.max_drawdown_pct}%</span>
                </div>
              </div>
            </div>

            {/* Out-Of-Sample Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-emerald)' }}>
                  OUT-OF-SAMPLE (TEST)
                </span>
                <span className="badge badge-bullish">{wfResult.out_of_sample.period}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Return:</span>
                  <span className="num-mono" style={{ fontWeight: 700, color: wfResult.out_of_sample.return_pct >= 0 ? 'var(--accent-emerald)' : 'var(--accent-ruby)' }}>
                    {wfResult.out_of_sample.return_pct > 0 ? '+' : ''}{wfResult.out_of_sample.return_pct}%
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Win Rate:</span>
                  <span className="num-mono" style={{ fontWeight: 600 }}>{wfResult.out_of_sample.win_rate}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Sharpe Ratio:</span>
                  <span className="num-mono" style={{ fontWeight: 600 }}>{wfResult.out_of_sample.sharpe}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Max Drawdown:</span>
                  <span className="num-mono" style={{ color: 'var(--accent-ruby)' }}>-{wfResult.out_of_sample.max_drawdown_pct}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
