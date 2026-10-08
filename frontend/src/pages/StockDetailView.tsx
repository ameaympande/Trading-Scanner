import React, { useEffect, useState } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  AlertCircle,
  BarChart2,
  CheckCircle2,
  ChevronDown,
  Compass,
  Layers,
  Search,
} from 'lucide-react';
import { fetchStockCandles, runBacktest } from '../api';
import { BacktestResponse, CandidateSetup, StockCandle } from '../types';

interface StockDetailViewProps {
  initialSymbol: string;
  setups: CandidateSetup[];
  onSimulateTrade: (setup: CandidateSetup) => void;
}

export const StockDetailView: React.FC<StockDetailViewProps> = ({
  initialSymbol,
  setups,
  onSimulateTrade,
}) => {
  const [symbol, setSymbol] = useState(initialSymbol || 'RELIANCE');
  const [candles, setCandles] = useState<StockCandle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backtestData, setBacktestData] = useState<BacktestResponse | null>(null);
  const [loadingBt, setLoadingBt] = useState(false);

  // Find if current symbol is an active candidate setup
  const activeSetup = setups.find((s) => s.symbol === symbol);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    fetchStockCandles(symbol, 250)
      .then((data) => {
        setCandles(data.candles);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    // Also run quick backtest stats for context
    setLoadingBt(true);
    runBacktest(symbol)
      .then((res) => {
        setBacktestData(res);
        setLoadingBt(false);
      })
      .catch(() => {
        setLoadingBt(false);
      });
  }, [symbol]);

  const latestCandle = candles[candles.length - 1];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Selector & Info Bar */}
      <div
        className="glass-panel"
        style={{
          padding: '20px',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              SELECT SYMBOL
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
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
                  fontSize: '1rem',
                  fontWeight: 700,
                  fontFamily: 'var(--font-heading)',
                  width: '140px',
                  textTransform: 'uppercase',
                }}
              />
              <button
                className="btn-secondary"
                onClick={() => setSymbol(symbol)}
                style={{ padding: '8px 12px' }}
              >
                <Search size={16} />
              </button>
            </div>
          </div>

          {latestCandle && (
            <div style={{ borderLeft: '1px solid var(--border-subtle)', paddingLeft: '16px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>LATEST CLOSE (NSE)</div>
              <div className="num-mono" style={{ fontSize: '1.4rem', fontWeight: 700, color: '#fff' }}>
                ₹{latestCandle.close.toFixed(2)}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                Date: {latestCandle.time} | Volume: {latestCandle.volume.toLocaleString('en-IN')}
              </div>
            </div>
          )}
        </div>

        {/* Setup Level Callout if detected */}
        {activeSetup ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              background: 'rgba(6, 182, 212, 0.1)',
              border: '1px solid rgba(6, 182, 212, 0.3)',
              padding: '12px 20px',
              borderRadius: 'var(--radius-md)',
            }}
          >
            <div>
              <span className="badge badge-bullish">ACTIVE SETUP</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-emerald)', marginTop: '2px' }}>
                Score: {activeSetup.score}/100
              </div>
            </div>
            <div className="num-mono" style={{ fontSize: '0.8rem', borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: '12px' }}>
              <div>Entry: ₹{activeSetup.entry_low.toFixed(0)}–{activeSetup.entry_high.toFixed(0)}</div>
              <div style={{ color: 'var(--accent-ruby)' }}>Stop: ₹{activeSetup.stop_loss.toFixed(0)}</div>
              <div style={{ color: 'var(--accent-emerald)' }}>Target: ₹{activeSetup.target1.toFixed(0)} (1:{activeSetup.risk_reward.toFixed(1)})</div>
            </div>
            <button
              className="btn-success"
              style={{ fontSize: '0.8rem', padding: '8px 14px' }}
              onClick={() => onSimulateTrade(activeSetup)}
            >
              Simulate Paper Trade
            </button>
          </div>
        ) : (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            No active pullback trigger on the current candle.
          </div>
        )}
      </div>

      {loading && (
        <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', color: 'var(--accent-cyan)' }}>
          Loading candlestick data & indicators for {symbol}...
        </div>
      )}

      {error && (
        <div className="glass-panel" style={{ padding: '30px', color: 'var(--accent-ruby)', textAlign: 'center' }}>
          <AlertCircle size={24} style={{ margin: '0 auto 8px' }} />
          {error}
        </div>
      )}

      {/* Main Candlestick & Moving Averages Chart */}
      {!loading && !error && candles.length > 0 && (
        <>
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  PRICE & MOVING AVERAGES
                </h3>
                <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem' }}>
                  <span style={{ color: '#38bdf8' }}>— SMA 20</span>
                  <span style={{ color: '#fbbf24' }}>— SMA 50</span>
                  <span style={{ color: '#f43f5e' }}>— SMA 200</span>
                  <span style={{ color: '#34d399' }}>-- EMA 20</span>
                </div>
              </div>
            </div>

            <div style={{ width: '100%', height: '360px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={candles}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                  <YAxis
                    stroke="var(--text-muted)"
                    fontSize={11}
                    domain={['auto', 'auto']}
                    tickFormatter={(v) => `₹${v}`}
                    orientation="right"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(14, 18, 27, 0.95)',
                      borderColor: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '8px',
                      fontSize: '0.75rem',
                    }}
                  />
                  {activeSetup && (
                    <>
                      <ReferenceLine y={activeSetup.stop_loss} stroke="var(--accent-ruby)" strokeDasharray="4 4" label={{ value: `Stop Loss ₹${activeSetup.stop_loss}`, fill: '#f43f5e', fontSize: 11 }} />
                      <ReferenceLine y={activeSetup.target1} stroke="var(--accent-emerald)" strokeDasharray="4 4" label={{ value: `Target ₹${activeSetup.target1}`, fill: '#10b981', fontSize: 11 }} />
                    </>
                  )}
                  <Line type="monotone" dataKey="close" stroke="#ffffff" dot={false} strokeWidth={2} name="Close" />
                  <Line type="monotone" dataKey="sma20" stroke="#38bdf8" dot={false} strokeWidth={1.5} name="SMA 20" />
                  <Line type="monotone" dataKey="sma50" stroke="#fbbf24" dot={false} strokeWidth={1.5} name="SMA 50" />
                  <Line type="monotone" dataKey="sma200" stroke="#f43f5e" dot={false} strokeWidth={2} name="SMA 200" />
                  <Line type="monotone" dataKey="ema20" stroke="#34d399" strokeDasharray="3 3" dot={false} strokeWidth={1.2} name="EMA 20" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* RSI and Volume Row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* RSI Chart */}
            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '10px' }}>
                RSI (14) MOMENTUM
              </div>
              <div style={{ width: '100%', height: '160px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={candles}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="time" hide />
                    <YAxis domain={[0, 100]} ticks={[30, 45, 70]} orientation="right" stroke="var(--text-muted)" fontSize={10} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(14, 18, 27, 0.95)',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderRadius: '8px',
                        fontSize: '0.75rem',
                      }}
                    />
                    <ReferenceLine y={70} stroke="rgba(244, 63, 94, 0.5)" strokeDasharray="3 3" />
                    <ReferenceLine y={45} stroke="rgba(6, 182, 212, 0.5)" strokeDasharray="3 3" />
                    <ReferenceLine y={30} stroke="rgba(16, 185, 129, 0.5)" strokeDasharray="3 3" />
                    <Area type="monotone" dataKey="rsi14" stroke="var(--accent-violet)" fill="rgba(139, 92, 246, 0.15)" strokeWidth={1.5} name="RSI 14" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Volume Chart */}
            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '10px' }}>
                DAILY VOLUME & RELATIVE TURNOVER
              </div>
              <div style={{ width: '100%', height: '160px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={candles}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="time" hide />
                    <YAxis orientation="right" stroke="var(--text-muted)" fontSize={10} tickFormatter={(v) => `${(v / 1e5).toFixed(0)}L`} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(14, 18, 27, 0.95)',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderRadius: '8px',
                        fontSize: '0.75rem',
                      }}
                    />
                    <Bar dataKey="volume" fill="rgba(56, 189, 248, 0.6)" name="Volume" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Historical Backtest Summary for this setup */}
          {backtestData && (
            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Layers size={16} color="var(--accent-cyan)" />
                  <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>
                    Historical Strategy Performance on {symbol} (TREND_PULLBACK_V1)
                  </span>
                </div>
                <span className="badge badge-cyan">Realistic Slippage & Fees Included</span>
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '12px',
                  background: 'rgba(0,0,0,0.25)',
                  padding: '14px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.8rem',
                }}
              >
                <div>
                  <div style={{ color: 'var(--text-muted)' }}>Total Strategy Return:</div>
                  <div className="num-mono" style={{ fontWeight: 700, fontSize: '1.1rem', color: backtestData.metrics.total_return_pct >= 0 ? 'var(--accent-emerald)' : 'var(--accent-ruby)' }}>
                    {backtestData.metrics.total_return_pct > 0 ? '+' : ''}{backtestData.metrics.total_return_pct}%
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)' }}>Win Rate:</div>
                  <div className="num-mono" style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                    {backtestData.metrics.win_rate_pct}% ({backtestData.metrics.winning_trades} / {backtestData.metrics.total_trades} trades)
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)' }}>Profit Factor:</div>
                  <div className="num-mono" style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                    {backtestData.metrics.profit_factor}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)' }}>Max Drawdown:</div>
                  <div className="num-mono" style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--accent-ruby)' }}>
                    -{backtestData.metrics.max_drawdown_pct}%
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)' }}>Sharpe Ratio:</div>
                  <div className="num-mono" style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                    {backtestData.metrics.sharpe_ratio}
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
