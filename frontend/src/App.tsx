import React, { useEffect, useState } from 'react';
import { fetchLatestScan, fetchPaperPortfolio, fetchScan, placePaperOrder } from './api';
import { Navbar } from './components/Navbar';
import { BacktestView } from './pages/BacktestView';
import { DashboardView } from './pages/DashboardView';
import { EdgeCenterView } from './pages/EdgeCenterView';
import { HealthView } from './pages/HealthView';
import { PaperTradingView } from './pages/PaperTradingView';
import { ResearchLabView } from './pages/ResearchLabView';
import { ScannerView } from './pages/ScannerView';
import { StockDetailView } from './pages/StockDetailView';
import { CandidateSetup, MarketRegime, PaperPortfolio } from './types';

export function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedStock, setSelectedStock] = useState('DIVISLAB');
  const [regime, setRegime] = useState<MarketRegime | null>(null);
  const [setups, setSetups] = useState<CandidateSetup[]>([]);
  const [paperPortfolio, setPaperPortfolio] = useState<PaperPortfolio | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [capital, setCapital] = useState(100000);
  const [riskPct, setRiskPct] = useState(0.0075);
  const [selectedUniverse, setSelectedUniverse] = useState('NIFTY_200');

  const loadScanData = async () => {
    setIsScanning(true);
    try {
      const data = await fetchScan({
        universe: 'NIFTY_200',
        capital,
        risk_pct: riskPct,
      });
      setRegime(data.regime);
      setSetups(data.setups);
      if (data.setups.length > 0) {
        setSelectedStock(data.setups[0].symbol);
      }
    } catch (e) {
      console.error('Scan load error:', e);
    } finally {
      setIsScanning(false);
    }
  };

  const loadPortfolio = async () => {
    try {
      const data = await fetchPaperPortfolio();
      setPaperPortfolio(data);
    } catch (e) {
      console.error('Portfolio load error:', e);
    }
  };

  useEffect(() => {
    loadScanData();
    loadPortfolio();
  }, []);

  const handleTriggerScan = async (universeOverride?: string) => {
    setIsScanning(true);
    const uni = universeOverride || selectedUniverse;
    if (universeOverride) {
      setSelectedUniverse(universeOverride);
    }
    try {
      const data = await fetchScan({
        universe: uni,
        capital,
        risk_pct: riskPct,
      });
      setRegime(data.regime);
      setSetups(data.setups);
      if (data.setups.length > 0) {
        setSelectedStock(data.setups[0].symbol);
      }
    } catch (e) {
      console.error('Trigger scan error:', e);
    } finally {
      setIsScanning(false);
    }
  };

  const handleSelectStock = (symbol: string) => {
    setSelectedStock(symbol);
    setActiveTab('stock-detail');
  };

  const handleSimulateTrade = async (setup: CandidateSetup) => {
    try {
      await placePaperOrder({
        symbol: setup.symbol,
        entry_price: setup.entry_low,
        quantity: setup.suggested_qty > 0 ? setup.suggested_qty : 5,
        stop_loss: setup.stop_loss,
        target1: setup.target1,
        target2: setup.target2,
        strategy: setup.strategy_name,
        score: setup.score,
      });
      await loadPortfolio();
      setActiveTab('paper-trading');
    } catch (e: any) {
      alert(`Could not place paper trade: ${e.message}`);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        regime={regime}
        onRefreshScan={handleTriggerScan}
        isScanning={isScanning}
      />

      <main style={{ maxWidth: '1440px', width: '100%', margin: '0 auto', padding: '28px 24px', flex: 1 }}>
        {activeTab === 'dashboard' && (
          <DashboardView
            regime={regime}
            setups={setups}
            paperPortfolio={paperPortfolio}
            onSelectStock={handleSelectStock}
            onNavigateTab={setActiveTab}
            onSimulateTrade={handleSimulateTrade}
          />
        )}

        {activeTab === 'scanner' && (
          <ScannerView
            setups={setups}
            onSelectStock={handleSelectStock}
            onSimulateTrade={handleSimulateTrade}
            capital={capital}
            setCapital={setCapital}
            riskPct={riskPct}
            setRiskPct={setRiskPct}
            selectedUniverse={selectedUniverse}
            setSelectedUniverse={setSelectedUniverse}
            onTriggerScan={handleTriggerScan}
            isScanning={isScanning}
          />
        )}

        {activeTab === 'edge-center' && <EdgeCenterView />}

        {activeTab === 'research-lab' && <ResearchLabView />}

        {activeTab === 'stock-detail' && (
          <StockDetailView
            initialSymbol={selectedStock}
            setups={setups}
            onSimulateTrade={handleSimulateTrade}
          />
        )}

        {activeTab === 'backtest' && <BacktestView />}

        {activeTab === 'paper-trading' && (
          <PaperTradingView
            portfolio={paperPortfolio}
            onRefresh={loadPortfolio}
          />
        )}

        {activeTab === 'health' && <HealthView />}
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '16px 24px',
          textAlign: 'center',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          background: 'rgba(7, 9, 14, 0.95)',
        }}
      >
        Quantitative Swing Research Platform • NSE India Equities • Historical performance is not indicative of future returns • Live execution disabled
      </footer>
    </div>
  );
}

export default App;
