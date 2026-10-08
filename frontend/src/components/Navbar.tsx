import React from 'react';
import {
  Activity,
  BarChart3,
  BrainCircuit,
  Compass,
  FileText,
  FlaskConical,
  Layers,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { MarketRegime } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  regime: MarketRegime | null;
  onRefreshScan: () => void;
  isScanning: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  regime,
  onRefreshScan,
  isScanning,
}) => {
  const regimeBadge = () => {
    if (!regime) return null;
    const isBull = regime.regime === 'BULLISH';
    const isBear = regime.regime === 'BEARISH';
    return (
      <div
        className={`badge ${
          isBull ? 'badge-bullish' : isBear ? 'badge-bearish' : 'badge-neutral'
        } pulse-glow`}
        title={`NIFTY 50 Score: ${regime.score > 0 ? '+' : ''}${regime.score.toFixed(2)}`}
      >
        <span
          style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            backgroundColor: isBull ? 'var(--accent-emerald)' : isBear ? 'var(--accent-ruby)' : 'var(--accent-amber)',
            display: 'inline-block',
          }}
        />
        NIFTY 50: {regime.regime}
      </div>
    );
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Compass },
    { id: 'scanner', label: 'Swing Scanner', icon: TrendingUp },
    { id: 'edge-center', label: 'Edge Center', icon: BrainCircuit },
    { id: 'research-lab', label: 'Research Lab', icon: FlaskConical },
    { id: 'stock-detail', label: 'Stock Charts', icon: BarChart3 },
    { id: 'backtest', label: 'Backtest Lab', icon: Layers },
    { id: 'paper-trading', label: 'Paper Trading', icon: Wallet },
    { id: 'health', label: 'Data & Rules', icon: ShieldCheck },
  ];

  return (
    <header
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(7, 9, 14, 0.92)',
        backdropFilter: 'blur(16px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: '1440px',
          margin: '0 auto',
          padding: '0 24px',
          height: '70px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Brand & Market Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #0284c7, #06b6d4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 15px rgba(6, 182, 212, 0.4)',
              }}
            >
              <Activity size={20} color="#fff" />
            </div>
            <div>
              <div
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: '1.15rem',
                  fontWeight: 700,
                  letterSpacing: '-0.02em',
                  background: 'linear-gradient(90deg, #f8fafc, #38bdf8)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                SWING RADAR
              </div>
              <div
                style={{
                  fontSize: '0.675rem',
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  fontWeight: 600,
                }}
              >
                NSE / BSE Quantitative Scanner
              </div>
            </div>
          </div>

          <div style={{ height: '24px', width: '1px', background: 'var(--border-subtle)' }} />

          {/* Regime Pill */}
          {regimeBadge()}
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-md)',
                  background: isActive ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  border: isActive ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid transparent',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <Icon
                  size={16}
                  color={isActive ? 'var(--accent-cyan)' : 'var(--text-muted)'}
                />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Action button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            className="btn-primary"
            onClick={onRefreshScan}
            disabled={isScanning}
            style={{ fontSize: '0.8rem', padding: '8px 14px' }}
          >
            <RefreshCw size={14} className={isScanning ? 'pulse-glow' : ''} />
            {isScanning ? 'Scanning...' : 'Run Scan'}
          </button>
        </div>
      </div>
    </header>
  );
};
