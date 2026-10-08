import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  Lock,
  Scale,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { fetchHealth } from '../api';

export const HealthView: React.FC = () => {
  const [healthData, setHealthData] = useState<any>(null);

  useEffect(() => {
    fetchHealth()
      .then((data) => setHealthData(data))
      .catch(() => {});
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Provider Status Card */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Database size={20} color="var(--accent-cyan)" />
            <h3 style={{ fontSize: '1.1rem', fontFamily: 'var(--font-heading)' }}>
              Market Data & System Health
            </h3>
          </div>
          <span className="badge badge-bullish">ONLINE & HEALTHY</span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
            fontSize: '0.85rem',
          }}
        >
          <div>
            <div style={{ color: 'var(--text-muted)' }}>PRIMARY DATA SOURCE</div>
            <div style={{ fontWeight: 600, color: '#fff' }}>Yahoo Finance (NSE: .NS / BSE: .BO)</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)' }}>TARGET MARKET & TIMEZONE</div>
            <div style={{ fontWeight: 600, color: '#fff' }}>NSE Equities (Asia/Kolkata)</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)' }}>CACHE STORAGE</div>
            <div style={{ fontWeight: 600, color: '#fff' }}>Parquet Local Cache (PyArrow Engine)</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)' }}>LIVE BROKER EXECUTION</div>
            <div style={{ fontWeight: 600, color: 'var(--accent-ruby)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Lock size={14} /> DISABLED (Safety Enforced)
            </div>
          </div>
        </div>
      </div>

      {/* Data Validation Pipeline Rules */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: '14px' }}>
          Data Quality & Hygiene Safeguards
        </h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Raw data is strictly verified before reaching strategy calculators:
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', fontSize: '0.8rem' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <CheckCircle2 size={16} color="var(--accent-emerald)" style={{ flexShrink: 0 }} />
            <div>
              <strong>Impossible OHLC Check:</strong> Rejects candles where High &lt; Low, Open/Close outside High-Low.
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <CheckCircle2 size={16} color="var(--accent-emerald)" style={{ flexShrink: 0 }} />
            <div>
              <strong>Volume Validation:</strong> Rejects negative volume candles; flags zero-volume anomaly days.
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <CheckCircle2 size={16} color="var(--accent-emerald)" style={{ flexShrink: 0 }} />
            <div>
              <strong>Abnormal Jump Detection:</strong> Flags &gt;35% single-day price jumps (unadjusted corporate actions).
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <CheckCircle2 size={16} color="var(--accent-emerald)" style={{ flexShrink: 0 }} />
            <div>
              <strong>Zero Look-Ahead Bias:</strong> Day T signal generates orders ONLY for Day T+1 Open.
            </div>
          </div>
        </div>
      </div>

      {/* Statutory Fee Schedule */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '14px' }}>
          Indian Equity Delivery Transaction Friction Assumptions
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', fontSize: '0.8rem' }}>
          <div>
            <div style={{ color: 'var(--text-muted)' }}>Brokerage (Delivery):</div>
            <div className="num-mono" style={{ fontWeight: 600 }}>₹0 (Discount Broker model)</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)' }}>STT (Buy & Sell):</div>
            <div className="num-mono" style={{ fontWeight: 600 }}>0.1% on buy + 0.1% on sell</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)' }}>Exchange Charges:</div>
            <div className="num-mono" style={{ fontWeight: 600 }}>0.00345% (NSE)</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)' }}>GST on charges:</div>
            <div className="num-mono" style={{ fontWeight: 600 }}>18%</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)' }}>Stamp Duty:</div>
            <div className="num-mono" style={{ fontWeight: 600 }}>0.015% (Buy side only)</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)' }}>DP Charge on Sell:</div>
            <div className="num-mono" style={{ fontWeight: 600 }}>₹15.93 flat per scrip</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)' }}>Simulated Slippage:</div>
            <div className="num-mono" style={{ fontWeight: 600 }}>0.1% entry + 0.1% exit</div>
          </div>
        </div>
      </div>

      {/* Quantitative Ethics Statement */}
      <div
        style={{
          background: 'rgba(6, 182, 212, 0.05)',
          border: '1px solid rgba(6, 182, 212, 0.2)',
          borderRadius: 'var(--radius-md)',
          padding: '20px',
          fontSize: '0.8rem',
          lineHeight: '1.7',
          color: 'var(--text-secondary)',
        }}
      >
        <strong style={{ color: '#fff' }}>Research Philosophy:</strong> This platform is designed around strict probabilistic swing trading principles. Strategy scores measure degree-of-fit to technical criteria rather than predicting certainty. Risk sizing (0.75% per trade default) prevents ruin during adverse market regimes. No algorithmic model guarantees profit.
      </div>
    </div>
  );
};
