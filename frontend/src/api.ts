import {
  BacktestResponse,
  EdgeCenterResponse,
  ExperimentRecord,
  FailureAnalysisResponse,
  MonteCarloResponse,
  PaperPortfolio,
  ScanResponse,
  StockChartResponse,
  WalkForwardResult,
} from './types';

const API_BASE = 'http://localhost:8000/api';

export async function fetchScan(params?: {
  universe?: string;
  top_n?: number;
  capital?: number;
  risk_pct?: number;
  only_affordable?: boolean;
}): Promise<ScanResponse> {
  const res = await fetch(`${API_BASE}/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      universe: params?.universe || 'NIFTY_200',
      top_n: params?.top_n || 10,
      capital: params?.capital || 100000,
      risk_pct: params?.risk_pct || 0.0075,
      only_affordable: params?.only_affordable || false,
      use_cache: true,
    }),
  });
  if (!res.ok) {
    throw new Error(`Scan failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchLatestScan(): Promise<ScanResponse> {
  const res = await fetch(`${API_BASE}/scan/latest`);
  if (!res.ok) {
    throw new Error(`Failed to fetch latest scan`);
  }
  return res.json();
}

export async function fetchStockCandles(
  symbol: string,
  days: number = 300
): Promise<StockChartResponse> {
  const res = await fetch(`${API_BASE}/stocks/${symbol}/ohlcv?days=${days}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch candles for ${symbol}`);
  }
  return res.json();
}

export async function runBacktest(
  symbol: string,
  capital: number = 100000,
  riskPct: number = 0.0075
): Promise<BacktestResponse> {
  const res = await fetch(`${API_BASE}/backtest/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbol,
      initial_capital: capital,
      risk_pct: riskPct,
      lookback_days: 600,
    }),
  });
  if (!res.ok) {
    throw new Error(`Backtest failed: ${res.statusText}`);
  }
  return res.json();
}

export async function runWalkForward(
  symbol: string,
  capital: number = 100000
): Promise<WalkForwardResult> {
  const res = await fetch(`${API_BASE}/backtest/walk-forward`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbol,
      initial_capital: capital,
      lookback_days: 800,
    }),
  });
  if (!res.ok) {
    throw new Error(`Walk forward failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchPaperPortfolio(): Promise<PaperPortfolio> {
  const res = await fetch(`${API_BASE}/paper/portfolio`);
  if (!res.ok) {
    throw new Error(`Failed to load paper portfolio`);
  }
  return res.json();
}

export async function placePaperOrder(payload: {
  symbol: string;
  entry_price: number;
  quantity: number;
  stop_loss: number;
  target1: number;
  target2?: number;
  strategy?: string;
  score?: number;
}) {
  const res = await fetch(`${API_BASE}/paper/order`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Order execution failed');
  }
  return res.json();
}

export async function closePaperPosition(position_id: string, exit_price: number) {
  const res = await fetch(`${API_BASE}/paper/close`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      position_id,
      exit_price,
      exit_reason: 'MANUAL',
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Position close failed');
  }
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchEdgeCenter(): Promise<EdgeCenterResponse> {
  const res = await fetch(`${API_BASE}/research/edge-center`);
  if (!res.ok) {
    throw new Error('Failed to fetch Edge Center status');
  }
  return res.json();
}

export async function fetchFailureAnalysis(): Promise<FailureAnalysisResponse> {
  const res = await fetch(`${API_BASE}/research/failure-analysis`);
  if (!res.ok) {
    throw new Error('Failed to fetch failure analysis');
  }
  return res.json();
}

export async function runMonteCarlo(
  symbol: string = 'RELIANCE',
  capital: number = 100000,
  riskPct: number = 0.0075,
  iterations: number = 500
): Promise<MonteCarloResponse> {
  const res = await fetch(`${API_BASE}/research/monte-carlo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbol,
      initial_capital: capital,
      risk_pct: riskPct,
      iterations,
    }),
  });
  if (!res.ok) {
    throw new Error('Monte Carlo simulation failed');
  }
  return res.json();
}

export async function fetchExperiments(): Promise<ExperimentRecord[]> {
  const res = await fetch(`${API_BASE}/research/experiments`);
  if (!res.ok) {
    throw new Error('Failed to fetch experiments');
  }
  return res.json();
}

export async function recordExperiment(payload: {
  strategy_name: string;
  universe: string;
  parameters: Record<string, any>;
  metrics: Record<string, any>;
  start_date: string;
  end_date: string;
  notes?: string;
}): Promise<ExperimentRecord> {
  const res = await fetch(`${API_BASE}/research/experiments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error('Failed to record experiment');
  }
  return res.json();
}

