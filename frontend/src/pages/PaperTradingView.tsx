import React, { useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  DollarSign,
  Plus,
  RefreshCw,
  Wallet,
  X,
} from 'lucide-react';
import { closePaperPosition, placePaperOrder } from '../api';
import { PaperPortfolio } from '../types';

interface PaperTradingViewProps {
  portfolio: PaperPortfolio | null;
  onRefresh: () => void;
}

export const PaperTradingView: React.FC<PaperTradingViewProps> = ({
  portfolio,
  onRefresh,
}) => {
  const [closingId, setClosingId] = useState<string | null>(null);
  const [exitPrice, setExitPrice] = useState<number>(0);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [newOrder, setNewOrder] = useState({
    symbol: 'TCS',
    entry_price: 3500,
    quantity: 10,
    stop_loss: 3420,
    target1: 3700,
  });
  const [actionError, setActionError] = useState<string | null>(null);

  const handleClose = async (posId: string) => {
    setActionError(null);
    try {
      await closePaperPosition(posId, exitPrice);
      setClosingId(null);
      onRefresh();
    } catch (err: any) {
      setActionError(err.message || 'Close failed');
    }
  };

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);
    try {
      await placePaperOrder(newOrder);
      setShowOrderModal(false);
      onRefresh();
    } catch (err: any) {
      setActionError(err.message || 'Failed to place order');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Portfolio Summary Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
        }}
      >
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>CURRENT PORTFOLIO VALUE</div>
          <div className="num-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-emerald)', marginTop: '6px' }}>
            ₹{portfolio?.current_equity.toLocaleString('en-IN') || '1,00,000'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Return: {portfolio?.total_return_pct || 0}%
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>AVAILABLE CASH</div>
          <div className="num-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: '#fff', marginTop: '6px' }}>
            ₹{portfolio?.cash_balance.toLocaleString('en-IN') || '1,00,000'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Invested: ₹{portfolio?.total_invested.toLocaleString('en-IN') || '0'}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>REALIZED P&L</div>
          <div className="num-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: (portfolio?.realized_pnl || 0) >= 0 ? 'var(--accent-emerald)' : 'var(--accent-ruby)', marginTop: '6px' }}>
            {(portfolio?.realized_pnl || 0) > 0 ? '+' : ''}₹{portfolio?.realized_pnl.toLocaleString('en-IN') || '0'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Fees Paid: ₹{portfolio?.total_fees_paid.toFixed(2) || '0'}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>WIN RATE (PAPER)</div>
          <div className="num-mono" style={{ fontSize: '1.6rem', fontWeight: 700, color: '#fff', marginTop: '6px' }}>
            {portfolio?.win_rate_pct || 0}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Closed Trades: {portfolio?.trade_history.length || 0}
          </div>
        </div>
      </div>

      {actionError && (
        <div className="glass-panel" style={{ padding: '14px 20px', color: 'var(--accent-ruby)', background: 'rgba(244, 63, 94, 0.1)' }}>
          {actionError}
        </div>
      )}

      {/* Open Positions Section */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
            Active Open Positions ({portfolio?.open_positions.length || 0})
          </div>
          <button className="btn-secondary" onClick={() => setShowOrderModal(true)} style={{ fontSize: '0.75rem', padding: '6px 12px' }}>
            <Plus size={14} /> Simulate Custom Order
          </button>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Entry Date</th>
              <th style={{ textAlign: 'right' }}>Entry Price</th>
              <th style={{ textAlign: 'right' }}>Qty</th>
              <th style={{ textAlign: 'right', color: 'var(--accent-ruby)' }}>Stop Loss</th>
              <th style={{ textAlign: 'right', color: 'var(--accent-emerald)' }}>Target 1</th>
              <th style={{ textAlign: 'right' }}>Current Price</th>
              <th style={{ textAlign: 'right' }}>Unrealized P&L</th>
              <th style={{ textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {!portfolio?.open_positions || portfolio.open_positions.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                  No open positions. Use the Scanner to identify setups and click "Trade" to simulate!
                </td>
              </tr>
            ) : (
              portfolio.open_positions.map((pos) => (
                <tr key={pos.id}>
                  <td style={{ fontWeight: 600, color: '#fff' }}>{pos.symbol}</td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{pos.entry_date}</td>
                  <td className="num-mono" style={{ textAlign: 'right' }}>₹{pos.entry_price.toFixed(2)}</td>
                  <td className="num-mono" style={{ textAlign: 'right', fontWeight: 600 }}>{pos.quantity}</td>
                  <td className="num-mono" style={{ textAlign: 'right', color: 'var(--accent-ruby)' }}>₹{pos.stop_loss.toFixed(2)}</td>
                  <td className="num-mono" style={{ textAlign: 'right', color: 'var(--accent-emerald)' }}>₹{pos.target1.toFixed(2)}</td>
                  <td className="num-mono" style={{ textAlign: 'right' }}>₹{pos.current_price.toFixed(2)}</td>
                  <td className="num-mono" style={{ textAlign: 'right', fontWeight: 600, color: pos.unrealized_pnl >= 0 ? 'var(--accent-emerald)' : 'var(--accent-ruby)' }}>
                    {pos.unrealized_pnl > 0 ? '+' : ''}₹{pos.unrealized_pnl.toFixed(2)} ({pos.unrealized_pnl_pct}%)
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {closingId === pos.id ? (
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center', justifyContent: 'center' }}>
                        <input
                          type="number"
                          placeholder="Exit ₹"
                          value={exitPrice || ''}
                          onChange={(e) => setExitPrice(Number(e.target.value))}
                          style={{ width: '80px', padding: '4px', background: 'var(--bg-surface-elevated)', color: '#fff', border: '1px solid var(--border-subtle)', borderRadius: '4px', fontSize: '0.75rem' }}
                        />
                        <button className="btn-success" style={{ padding: '4px 8px', fontSize: '0.7rem' }} onClick={() => handleClose(pos.id)}>
                          Confirm
                        </button>
                        <button className="btn-secondary" style={{ padding: '4px 8px', fontSize: '0.7rem' }} onClick={() => setClosingId(null)}>
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.725rem' }}
                        onClick={() => {
                          setClosingId(pos.id);
                          setExitPrice(pos.current_price);
                        }}
                      >
                        Close Position
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Closed Trades History */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', fontWeight: 600, fontSize: '0.95rem' }}>
          Completed Paper Trades History ({portfolio?.trade_history.length || 0})
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Entry Date</th>
              <th>Exit Date</th>
              <th style={{ textAlign: 'right' }}>Entry (₹)</th>
              <th style={{ textAlign: 'right' }}>Exit (₹)</th>
              <th style={{ textAlign: 'right' }}>Qty</th>
              <th style={{ textAlign: 'right' }}>Net P&L (₹)</th>
              <th style={{ textAlign: 'right' }}>P&L %</th>
              <th style={{ textAlign: 'right' }}>Fees (₹)</th>
              <th>Exit Reason</th>
            </tr>
          </thead>
          <tbody>
            {!portfolio?.trade_history || portfolio.trade_history.length === 0 ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                  No closed trades recorded yet.
                </td>
              </tr>
            ) : (
              portfolio.trade_history.map((t, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 600 }}>{t.symbol}</td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{t.entry_date}</td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{t.exit_date}</td>
                  <td className="num-mono" style={{ textAlign: 'right' }}>₹{t.entry_price.toFixed(2)}</td>
                  <td className="num-mono" style={{ textAlign: 'right' }}>₹{t.exit_price.toFixed(2)}</td>
                  <td className="num-mono" style={{ textAlign: 'right' }}>{t.quantity}</td>
                  <td className="num-mono" style={{ textAlign: 'right', fontWeight: 600, color: t.net_pnl >= 0 ? 'var(--accent-emerald)' : 'var(--accent-ruby)' }}>
                    {t.net_pnl > 0 ? '+' : ''}₹{t.net_pnl.toFixed(2)}
                  </td>
                  <td className="num-mono" style={{ textAlign: 'right', color: t.net_pnl_pct >= 0 ? 'var(--accent-emerald)' : 'var(--accent-ruby)' }}>
                    {t.net_pnl_pct > 0 ? '+' : ''}{t.net_pnl_pct.toFixed(2)}%
                  </td>
                  <td className="num-mono" style={{ textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    ₹{t.fees.toFixed(2)}
                  </td>
                  <td>
                    <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>{t.exit_reason}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Manual Order Modal */}
      {showOrderModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.75)',
            backdropFilter: 'blur(8px)',
            zIndex: 100,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
          onClick={() => setShowOrderModal(false)}
        >
          <div
            className="glass-panel"
            style={{ maxWidth: '450px', width: '100%', padding: '24px' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.2rem', fontFamily: 'var(--font-heading)' }}>Simulate Paper Trade</h3>
              <button style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }} onClick={() => setShowOrderModal(false)}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreateOrder} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Symbol</label>
                <input
                  type="text"
                  required
                  value={newOrder.symbol}
                  onChange={(e) => setNewOrder({ ...newOrder, symbol: e.target.value.toUpperCase() })}
                  style={{ width: '100%', padding: '8px', background: 'var(--bg-surface-elevated)', color: '#fff', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Entry Price (₹)</label>
                  <input
                    type="number"
                    step="0.05"
                    required
                    value={newOrder.entry_price}
                    onChange={(e) => setNewOrder({ ...newOrder, entry_price: Number(e.target.value) })}
                    style={{ width: '100%', padding: '8px', background: 'var(--bg-surface-elevated)', color: '#fff', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Quantity</label>
                  <input
                    type="number"
                    required
                    value={newOrder.quantity}
                    onChange={(e) => setNewOrder({ ...newOrder, quantity: Number(e.target.value) })}
                    style={{ width: '100%', padding: '8px', background: 'var(--bg-surface-elevated)', color: '#fff', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}
                  />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Stop Loss (₹)</label>
                  <input
                    type="number"
                    step="0.05"
                    required
                    value={newOrder.stop_loss}
                    onChange={(e) => setNewOrder({ ...newOrder, stop_loss: Number(e.target.value) })}
                    style={{ width: '100%', padding: '8px', background: 'var(--bg-surface-elevated)', color: '#fff', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Target (₹)</label>
                  <input
                    type="number"
                    step="0.05"
                    required
                    value={newOrder.target1}
                    onChange={(e) => setNewOrder({ ...newOrder, target1: Number(e.target.value) })}
                    style={{ width: '100%', padding: '8px', background: 'var(--bg-surface-elevated)', color: '#fff', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}
                  />
                </div>
              </div>
              <button type="submit" className="btn-success" style={{ marginTop: '10px', padding: '10px' }}>
                Place Simulated Trade
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
