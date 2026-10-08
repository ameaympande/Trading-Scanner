export interface CandidateSetup {
  symbol: string;
  company_name: string;
  strategy_name: string;
  direction: string;
  timestamp: string;
  current_price: number;
  entry_low: number;
  entry_high: number;
  stop_loss: number;
  target1: number;
  target2: number;
  risk_reward: number;
  score: number;
  atr: number;
  rsi: number;
  relative_volume: number;
  market_regime: string;
  expected_holding_period: string;
  reasons: string[];
  invalidation: string;
  score_breakdown: Record<string, number>;
  sector: string;
  suggested_qty: number;
  position_value: number;
  setup_grade?: string;
  meta_score?: number;
  ml_prob_pct?: number;
  expected_value_r?: number;
}

export interface MarketRegime {
  benchmark_symbol: string;
  regime: string;
  close_price: number;
  score: number;
  reasons: string[];
  timestamp: string;
}

export interface ScanResponse {
  regime: MarketRegime;
  stats: {
    scanned: number;
    passed: number;
    execution_time_seconds: number;
    data_source: string;
    universe: string;
  };
  setups: CandidateSetup[];
}

export interface StockCandle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma20: number | null;
  sma50: number | null;
  sma200: number | null;
  ema20: number | null;
  ema50: number | null;
  rsi14: number | null;
  atr14: number | null;
}

export interface StockChartResponse {
  symbol: string;
  candles: StockCandle[];
  is_valid: boolean;
  anomalies: string[];
}

export interface SimulatedTrade {
  symbol: string;
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  stop_loss: number;
  target1: number;
  quantity: number;
  gross_pnl: number;
  net_pnl: number;
  net_pnl_pct: number;
  holding_days: number;
  exit_reason: string;
  friction_cost: number;
}

export interface BacktestMetrics {
  initial_capital: number;
  final_equity: number;
  total_return_pct: number;
  cagr_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  profit_factor: number;
  expectancy_per_trade: number;
  average_trade_pnl_pct: number;
  average_win_pct: number;
  average_loss_pct: number;
  win_loss_ratio: number;
  largest_win_pct: number;
  largest_loss_pct: number;
  max_consecutive_losses: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  average_holding_period_days: number;
  total_turnover: number;
  total_transaction_costs: number;
  equity_curve: { date: string; equity: number; drawdown_pct: number }[];
  monthly_returns: Record<string, Record<string, number>>;
  annual_returns: Record<string, number>;
}

export interface BacktestResponse {
  strategy_name: string;
  symbol: string;
  start_date: string;
  end_date: string;
  metrics: BacktestMetrics;
  trades: SimulatedTrade[];
  warnings: string[];
  disclaimer: string;
}

export interface WalkForwardResult {
  symbol: string;
  strategy: string;
  in_sample: {
    period: string;
    return_pct: number;
    sharpe: number;
    win_rate: number;
    total_trades: number;
    max_drawdown_pct: number;
  };
  out_of_sample: {
    period: string;
    return_pct: number;
    sharpe: number;
    win_rate: number;
    total_trades: number;
    max_drawdown_pct: number;
  };
  robustness_ratio: number;
  warning: string;
}

export interface PaperPosition {
  id: string;
  symbol: string;
  entry_date: string;
  entry_price: number;
  quantity: number;
  stop_loss: number;
  target1: number;
  target2: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  strategy: string;
  score: number;
  status: string;
}

export interface PaperTradeHistory {
  id: string;
  symbol: string;
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  net_pnl: number;
  net_pnl_pct: number;
  fees: number;
  exit_reason: string;
}

export interface PaperPortfolio {
  initial_capital: number;
  cash_balance: number;
  current_equity: number;
  total_invested: number;
  total_current_value: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_return_pct: number;
  total_fees_paid: number;
  win_rate_pct: number;
  open_positions: PaperPosition[];
  trade_history: PaperTradeHistory[];
}

export interface EdgeCenterResponse {
  timestamp: string;
  regime: {
    state: string;
    benchmark_close: number;
    nifty_20d_return: number;
    rsi14: number;
    adx14: number;
    reasons: string[];
    recommendation: string;
  };
  drawdown_protection: {
    mode: string;
    drawdown_pct: number;
    max_positions: number;
    risk_multiplier: number;
    message: string;
  };
  champion_model: {
    model_id: string;
    algorithm: string;
    version: string;
    brier_score: number;
    expected_value_r: number;
    win_rate_estimate_pct: number;
    is_calibrated: boolean;
    calibration_method: string;
    features_count: number;
  };
  edge_decay: {
    is_decay_detected: boolean;
    sample_size: number;
    win_rate_recent_pct: number;
    expectancy_recent_r: number;
    baseline_expectancy_r: number;
    warning_message: string | null;
  };
  drift_status: {
    is_drift_detected: boolean;
    drift_score: number;
    recommendation: string;
  };
  top_failure_reasons: {
    reason: string;
    pct: number;
    solution: string;
  }[];
}

export interface FailureAnalysisResponse {
  total_failures_analyzed: number;
  categories: {
    label: string;
    count: number;
    pct_of_total_losses: number;
    avg_mae_r: number;
    avg_bars_to_failure: number;
    description: string;
  }[];
  key_takeaway: string;
}

export interface MonteCarloResponse {
  symbol: string;
  iterations: number;
  median_max_drawdown_pct: number;
  drawdown_95th_percentile_pct: number;
  worst_case_drawdown_pct: number;
  risk_of_ruin_pct: number;
  median_ending_equity: number;
  equity_10th_percentile: number;
  equity_90th_percentile: number;
  expectancy_ci: {
    estimate: number;
    lower_bound_95: number;
    upper_bound_95: number;
  };
  win_rate_ci: {
    estimate: number;
    lower_bound_95: number;
    upper_bound_95: number;
  };
  profit_factor_ci: {
    estimate: number;
    lower_bound_95: number;
    upper_bound_95: number;
  };
  sample_equity_curves: number[][];
}

export interface ExperimentRecord {
  experiment_id: string;
  strategy_name: string;
  universe: string;
  parameters: Record<string, any>;
  metrics: Record<string, any>;
  start_date: string;
  end_date: string;
  timestamp: string;
  notes: string;
}

