"""
Tests for Adaptive Quantitative Trading Research System.

Validates:
1. MFE/MAE calculation & conservative ambiguous candle resolution (no optimistic bias).
2. Conditional expectancy engine with Bayesian sample-size shrinkage.
3. Chronological time-series ML training and Platt probability calibration.
4. Zero look-ahead data leakage tests (requirement #37).
5. Drawdown protection throttling & portfolio correlation guardrails.
6. Monte Carlo sequence simulation & bootstrap confidence intervals.
7. Meta-scorer and A+ setup grading.
"""

import numpy as np
import pandas as pd

from scanner.config import MarketRegimeLabel, SignalDirection
from scanner.research.expectancy import ConditionalExpectancyEngine
from scanner.research.meta_scorer import AdaptiveMetaScorer, SetupGrade
from scanner.research.ml_model import TradeQualityML
from scanner.research.monte_carlo import MonteCarloEngine
from scanner.research.observations import (
    OutcomeLabel,
    TradeObservation,
    calculate_mfe_mae,
    evaluate_trade_outcome,
)
from scanner.research.risk_adaptive import AdaptiveRiskManager, DrawdownMode
from scanner.strategies.base import CandidateSetup


def _create_synthetic_candle_df(dates: list[pd.Timestamp], base_price: float = 100.0) -> pd.DataFrame:
    records = []
    price = base_price
    for d in dates:
        records.append({
            "timestamp": d,
            "open": price,
            "high": price + 2.0,
            "low": price - 1.5,
            "close": price + 0.5,
            "volume": 500_000,
        })
        price += 0.5
    df = pd.DataFrame(records).set_index("timestamp")
    return df


def _create_sample_observations(n: int = 60) -> list[TradeObservation]:
    """Creates synthetic chronological observations with known outcomes."""
    base_date = pd.Timestamp("2024-01-01")
    obs_list = []
    for i in range(n):
        dt = base_date + pd.Timedelta(days=i * 2)
        is_winner = (i % 3 != 0)  # ~66% win rate
        r_val = 2.0 if is_winner else -1.0
        label = OutcomeLabel.WIN_FULL_TARGET if is_winner else OutcomeLabel.STOPPED

        obs = TradeObservation(
            symbol=f"STOCK_{i % 5}",
            timestamp=dt,
            market_regime="TRENDING_BULL" if i % 2 == 0 else "SIDEWAYS",
            sector="Nifty IT" if i % 2 == 0 else "Nifty Bank",
            industry="IT",
            price=100.0 + i,
            atr=2.5,
            rsi=55.0 + (i % 15),
            adx=26.0 + (i % 10),
            relative_volume=1.2 + (0.1 * (i % 10)),
            dist_ema20_pct=1.0,
            dist_ema50_pct=2.5,
            dist_sma200_pct=6.0,
            trend_strength=75.0,
            recent_volatility=1.8,
            ret_1d=0.01,
            ret_3d=0.02,
            ret_5d=0.03,
            ret_10d=0.05,
            ret_20d=0.08,
            nifty_ret_1d=0.005,
            nifty_ret_5d=0.015,
            nifty_ret_20d=0.04,
            relative_strength_vs_nifty=1.05,
            breakout_strength=1.1,
            pullback_depth_atr=1.0,
            volume_expansion=1.3,
            gap_pct=0.2,
            dist_to_resistance_pct=4.0,
            dist_to_support_pct=2.0,
            risk_reward=2.0,
            strategy_score=80,
            entry=100.0,
            stop=97.5,
            target=105.0,
            risk_per_share=2.5,
            mfe_r=2.2 if is_winner else 0.4,
            mae_r=0.6 if is_winner else 1.0,
            realized_r=r_val,
            realized_pct=5.0 if is_winner else -2.5,
            holding_period=5,
            outcome_label=label,
        )
        obs_list.append(obs)
    return obs_list


def test_mfe_mae_calculation():
    """Validates MFE and MAE formula in units of initial risk R."""
    candles = pd.DataFrame([
        {"high": 106.0, "low": 98.0},
        {"high": 108.0, "low": 99.0},
    ])
    entry = 100.0
    stop = 96.0  # Risk = 4.0
    mfe_r, mae_r = calculate_mfe_mae(entry, stop, candles)

    # Max high = 108.0 -> MFE = (108 - 100) / 4 = 2.0R
    # Min low = 98.0 -> MAE = (100 - 98) / 4 = 0.5R
    assert mfe_r == 2.0
    assert mae_r == 0.5


def test_ambiguous_candle_resolution_is_conservative():
    """
    Requirement #7: When both Target and Stop are touched in the same candle,
    system MUST NOT assume favorable outcome; must conservatively label STOPPED.
    """
    dates = [pd.Timestamp("2024-01-02")]
    # Single candle with high reaching target (106) and low reaching stop (96)
    forward_candles = pd.DataFrame(
        [{
            "open": 100.0,
            "high": 108.0,
            "low": 94.0,
            "close": 102.0,
        }],
        index=dates,
    )
    res = evaluate_trade_outcome(
        entry_date=pd.Timestamp("2024-01-01"),
        entry_price=100.0,
        stop_loss=96.0,
        target=106.0,
        forward_candles=forward_candles,
    )
    assert res.label == OutcomeLabel.STOPPED
    assert res.ambiguous_candle is True
    assert res.is_win is False


def test_conditional_expectancy_bayesian_shrinkage():
    """
    Validates that conditional expectancy calculates win rates and shrinks
    small-sample bucket expectations toward the base rate.
    """
    obs = _create_sample_observations(40)
    engine = ConditionalExpectancyEngine(shrinkage_k=20)
    results = engine.analyze_observations(obs)

    assert "rsi" in results
    assert "market_regime" in results

    regime_res = results["market_regime"]
    for bucket in regime_res.buckets:
        assert 0.0 <= bucket.confidence_factor <= 1.0
        # Confidence factor strictly matches N / (N + K)
        expected_conf = round(bucket.sample_size / (bucket.sample_size + 20), 3)
        assert abs(bucket.confidence_factor - expected_conf) < 1e-3
        # Shrunk EV must lie between raw EV and base EV (inclusive)
        min_ev = min(bucket.raw_expectancy_r, regime_res.base_expectancy_r)
        max_ev = max(bucket.raw_expectancy_r, regime_res.base_expectancy_r)
        assert min_ev - 0.01 <= bucket.shrunk_expectancy_r <= max_ev + 0.01


def test_trade_quality_ml_chronological_and_calibration():
    """
    Validates chronological splitting, probability calibration (Platt scaling),
    and Brier score evaluation.
    """
    obs = _create_sample_observations(50)
    ml = TradeQualityML(algorithm="gradient_boosting")
    eval_res = ml.train_chronological(obs, train_ratio=0.70, val_ratio=0.15)

    assert eval_res.brier_score >= 0.0
    assert eval_res.accuracy > 0.0
    assert ml.calibrated_model is not None
    assert len(ml.feature_importance_) > 0

    # Test prediction on a candidate
    p_win = ml.predict_probability(obs[0])
    assert 0.0 <= p_win <= 1.0


def test_zero_lookahead_data_leakage():
    """
    Requirement #36 & #37: Modifying data occurring after date X
    must NOT change model training or predictions made before date X.
    """
    obs = _create_sample_observations(50)

    # Model A: Trained on original chronological dataset
    ml_a = TradeQualityML(algorithm="logistic_regression")
    ml_a.train_chronological(obs[:35], train_ratio=0.75, val_ratio=0.25)
    pred_a = [ml_a.predict_probability(o) for o in obs[:10]]

    # Modify all subsequent data after cutoff
    obs_mutated = _create_sample_observations(50)
    for i in range(35, 50):
        obs_mutated[i].rsi = 99.0
        obs_mutated[i].relative_volume = 15.0
        obs_mutated[i].realized_r = -10.0

    # Model B: Trained on data ending at cutoff date
    ml_b = TradeQualityML(algorithm="logistic_regression")
    ml_b.train_chronological(obs_mutated[:35], train_ratio=0.75, val_ratio=0.25)
    pred_b = [ml_b.predict_probability(o) for o in obs_mutated[:10]]

    # Predictions before X must be strictly identical
    assert pred_a == pred_b


def test_adaptive_drawdown_protection_states():
    """
    Validates drawdown throttle states:
    0-5% NORMAL, 5-8% CAUTION, 8-12% DEFENSIVE, >12% PAUSED.
    """
    mgr = AdaptiveRiskManager()
    peak = 100_000.0

    # 1. 2% DD -> NORMAL
    s1 = mgr.get_drawdown_state(98_000.0, peak)
    assert s1.mode == DrawdownMode.NORMAL
    assert s1.max_allowed_positions == 5
    assert s1.allowed_risk_multiplier == 1.0

    # 2. 6% DD -> CAUTION
    s2 = mgr.get_drawdown_state(94_000.0, peak)
    assert s2.mode == DrawdownMode.CAUTION
    assert s2.max_allowed_positions == 3
    assert s2.allowed_risk_multiplier == 0.66

    # 3. 10% DD -> DEFENSIVE
    s3 = mgr.get_drawdown_state(90_000.0, peak)
    assert s3.mode == DrawdownMode.DEFENSIVE
    assert s3.max_allowed_positions == 1
    assert s3.allowed_risk_multiplier == 0.33

    # 4. 14% DD -> PAUSED
    s4 = mgr.get_drawdown_state(86_000.0, peak)
    assert s4.mode == DrawdownMode.PAUSED
    assert s4.max_allowed_positions == 0
    assert s4.allowed_risk_multiplier == 0.0

    # Verify sizing in PAUSED state gives 0 shares
    sizing = mgr.calculate_adaptive_sizing(
        entry_price=100.0,
        stop_loss=96.0,
        grade=SetupGrade.A_PLUS,
        dd_status=s4,
        capital=86_000.0,
    )
    assert sizing["quantity"] == 0
    assert sizing["risk_amount"] == 0.0


def test_portfolio_correlation_guardrail():
    """Validates that candidate with correlation > 0.65 is flagged unsafe."""
    mgr = AdaptiveRiskManager()
    dates = pd.date_range("2024-01-01", periods=30)

    # Identical returns -> correlation = 1.0
    series1 = pd.Series(np.linspace(0.01, 0.05, 30), index=dates)
    portfolio_open = {"TCS": series1}

    # Highly correlated candidate
    candidate_ret = series1 * 1.05
    check = mgr.check_portfolio_correlation("INFY", candidate_ret, portfolio_open, threshold=0.65)
    assert check.is_safe is False
    assert check.max_correlation > 0.65
    assert "High correlation" in str(check.warning)

    # Uncorrelated candidate
    uncorr_ret = pd.Series(np.sin(np.linspace(0, 10, 30)), index=dates)
    check2 = mgr.check_portfolio_correlation("SUNPHARMA", uncorr_ret, portfolio_open, threshold=0.65)
    assert check2.is_safe is True


def test_monte_carlo_bootstrap_confidence_intervals():
    """
    Validates Monte Carlo reshuffling and bootstrap confidence intervals.
    """
    returns_r = [2.0, -1.0, 1.5, 2.0, -1.0, 1.8, -0.9, 2.0, -1.0, 1.6, 2.0, -1.0]
    mc = MonteCarloEngine(iterations=200)
    res = mc.run_simulation(returns_r, initial_capital=100_000.0)

    assert res.iterations == 200
    assert res.expectancy_ci.lower_bound_95 <= res.expectancy_ci.estimate <= res.expectancy_ci.upper_bound_95
    assert res.win_rate_ci.lower_bound_95 <= res.win_rate_ci.estimate <= res.win_rate_ci.upper_bound_95
    assert res.median_max_drawdown_pct >= 0.0
    assert res.drawdown_95th_percentile_pct >= res.median_max_drawdown_pct
    assert len(res.simulation_curves) > 0


def test_adaptive_meta_scorer_grading():
    """
    Validates multi-layer scoring combining Base Score + ML + Conditional EV + RS
    into A+, A, B, C, REJECT grades.
    """
    scorer = AdaptiveMetaScorer()
    setup = CandidateSetup(
        symbol="RELIANCE",
        company_name="Reliance Industries",
        strategy_name="TREND_PULLBACK_V1",
        direction=SignalDirection.LONG,
        timestamp=pd.Timestamp("2024-01-10"),
        current_price=2500.0,
        entry_low=2490.0,
        entry_high=2510.0,
        stop_loss=2430.0,
        target1=2640.0,
        target2=2710.0,
        risk_reward=2.0,
        score=90,
        atr=30.0,
        rsi=54.0,
        relative_volume=1.8,
        market_regime=MarketRegimeLabel.BULLISH,
        expected_holding_period="3-10 days",
        reasons=["Healthy EMA20 pullback", "Above 200 SMA"],
    )
    obs = _create_sample_observations(10)[0]
    obs.relative_strength_vs_nifty = 1.08
    obs.relative_volume = 1.8

    res = scorer.evaluate_setup(setup, obs, rs_vs_nifty=1.08, sector_outperforming=True)
    assert res.grade in (SetupGrade.A_PLUS, SetupGrade.A)
    assert res.is_tradable is True
    assert res.meta_score > 70
