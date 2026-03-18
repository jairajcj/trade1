"""
TradeIntel Pro — Live Trading Intelligence Dashboard
Run: python -m streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import pytz

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="TradeIntel Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Persistence: Get last viewed ticker from URL
if 'ticker' in st.query_params:
    st.session_state['last_ticker'] = st.query_params['ticker']
from config import MARKETS, INDICES, COLORS, REFRESH_INTERVAL, CURRENCY_SYMBOLS
from core.data_engine import (
    fetch_stock_data, fetch_live_price,
    fetch_performance, fetch_indices_data,
    search_tickers, get_commodity_in_local_currencies,
)
from core.technical_engine import (
    compute_all_indicators, get_oscillator_summary,
    get_ma_summary, get_overall_rating, get_support_resistance,
)
from core.ml_engine import get_ml_results
from core.news_engine import fetch_ticker_news, fetch_market_news, compute_sentiment_score
from core.signals import generate_master_signal, get_trade_plan
from core import charts

IST = pytz.timezone("Asia/Kolkata")



def get_currency(ticker):
    """Returns the currency symbol for a given ticker."""
    t = ticker.upper()
    if t.endswith(".NS") or t.endswith(".BO"):
        return "₹"
    if "INR" in t:
        return "₹"
    if "GBP" in t:
        return "£"
    if "EUR" in t:
        return "€"
    if "JPY" in t:
        return "¥"
    return "$"  # default USD


# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📈 TradeIntel Pro")
    st.caption("Live Multi-Market Intelligence")
    st.divider()

    # Search bar
    st.markdown("**🔍 Search Any Asset**")
    persisted_ticker = st.session_state.get('last_ticker', '')
    search_query = st.text_input(
        "Search",
        placeholder="Type anything... ITC, Tesla, Gold, EURUSD",
        label_visibility="collapsed",
    )

    st.divider()

    if search_query and len(search_query.strip()) >= 2:
        # LIVE Yahoo Finance search — covers EVERYTHING
        results = search_tickers(search_query.strip())

        if results:
            options = [
                f"{r['name']} ({r['symbol']}) — {r['type']} · {r['exchange']}"
                for r in results
            ]
            selected_option = st.selectbox(
                f"📊 {len(results)} results found",
                options,
            )
            # Extract the ticker from the selected option
            idx = options.index(selected_option)
            selected_ticker = results[idx]["symbol"]
            selected_name = results[idx]["name"]
            selected_market = results[idx]["type"]
        else:
            # Fallback: use raw input as ticker
            selected_ticker = search_query.strip().upper()
            selected_name = selected_ticker
            selected_market = "Unknown"
            st.caption(f"Trying: **{selected_ticker}**")
    else:
        # No search → browse predefined popular lists
        # Persist Market selection
        market_options = list(MARKETS.keys())
        last_t = st.session_state.get('last_ticker', '')
        default_m_idx = 0
        for m_idx, m_name in enumerate(market_options):
            if any(last_t == sym for sym in MARKETS[m_name].keys()):
                default_m_idx = m_idx
                break
        selected_market = st.selectbox("🌍 Market", market_options, index=default_m_idx)
        tickers_dict = MARKETS[selected_market]
        options = sorted([f"{name} ({sym})" for sym, name in tickers_dict.items()])
        # Find index of last seen ticker to persist selection
        default_idx = 0
        last_t = st.session_state.get('last_ticker', '')
        for idx, opt in enumerate(options):
            if f"({last_t})" in opt:
                default_idx = idx
                break
        selected_label = st.selectbox("📊 Select Asset", options, index=default_idx)
        # Reverse lookup
        label_to_ticker = {f"{name} ({sym})": sym for sym, name in tickers_dict.items()}
        selected_ticker = label_to_ticker[selected_label]
        selected_name = tickers_dict[selected_ticker]

    currency = get_currency(selected_ticker)
    # Persist selection in URL
    st.query_params['ticker'] = selected_ticker

    st.divider()
    chart_period = st.selectbox("📅 Chart Period", ["3mo", "6mo", "1y", "2y"], index=2)
    show_bb = st.toggle("Bollinger Bands", value=True)
    show_ema = st.toggle("EMA / SMA Lines", value=True)
    show_vol = st.toggle("Volume Subplot", value=True)

    st.divider()
    auto_refresh = st.toggle("🔄 Auto Refresh (60s)", value=False)

    st.divider()
    now_ist = datetime.now(IST)
    st.markdown(f"**🕒 {now_ist.strftime('%H:%M:%S IST')}**")
    st.caption(now_ist.strftime("%A, %d %b %Y"))


# ═══════════════════════════════════════════════════════════════
# HEADER — Live Indices Bar
# ═══════════════════════════════════════════════════════════════
st.markdown("## 📈 TradeIntel Pro — Live Dashboard")

with st.spinner("Loading indices..."):
    indices_data = fetch_indices_data(INDICES)

if indices_data:
    cols = st.columns(min(len(indices_data), 7))
    for i, (name, data) in enumerate(indices_data.items()):
        if i < len(cols):
            with cols[i]:
                sym = CURRENCY_SYMBOLS.get(name, "$")
                st.metric(
                    label=name,
                    value=f"{sym}{data['price']:,.2f}",
                    delta=f"{data['change_pct']:+.2f}%",
                )

st.divider()


# ═══════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════
with st.spinner(f"⚡ Fetching live data for {selected_name}..."):
    df_raw = fetch_stock_data(selected_ticker, period=chart_period)
    live = fetch_live_price(selected_ticker)
    perf = fetch_performance(selected_ticker)

if df_raw.empty:
    st.error(f"❌ No data for **{selected_ticker}**. Check the ticker (Use Yahoo Finance format, e.g. RELIANCE.NS, GC=F, EURUSD=X)")
    st.stop()

df = compute_all_indicators(df_raw)


# ═══════════════════════════════════════════════════════════════
# LIVE PRICE BAR
# ═══════════════════════════════════════════════════════════════
if live:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(f"💰 Price ({currency})", f"{currency}{live['price']:,.2f}")
    arrow = "▲" if live['change_pct'] >= 0 else "▼"
    c2.metric("Change", f"{currency}{live['change']:+,.2f}", f"{arrow} {abs(live['change_pct']):.2f}%")
    c3.metric("Day High", f"{currency}{live['high']:,.2f}")
    c4.metric("Day Low", f"{currency}{live['low']:,.2f}")
    c5.metric("Open", f"{currency}{live['open']:,.2f}")
    vol = live.get("volume", 0)
    vol_str = f"{vol/1e6:.1f}M" if vol > 1e6 else f"{vol:,}"
    c6.metric("Volume", vol_str)

# Gold/Silver: show REAL prices in INR & AED
# Market Detection
selected_ticker_upper = selected_ticker.upper()
is_dubai_gold = 'DUBAI' in selected_name.upper() and 'GOLD' in selected_name.upper()
is_gold = is_dubai_gold or selected_ticker_upper in ['GC=F', 'GLD', 'IAU', 'GOLDBEES.NS', 'GOLD']
is_silver = selected_ticker_upper in ['SI=F', 'SLV', 'SILVERBEES.NS']

if is_gold or is_silver:
    commodity_base = 'GC=F' if is_gold else 'SI=F'
    metal_name = '🥇 Dubai Gold' if is_dubai_gold else ('🥇 Gold (India)' if is_gold else '🥈 Silver')
    converted = get_commodity_in_local_currencies(commodity_base, is_dubai=is_dubai_gold)
    if converted:
        if is_dubai_gold:
            st.markdown(f'## {metal_name}: AED {converted["aed_24k"]:,.0f}')
            c1, c2, c3 = st.columns(3)
            c1.metric('24K Dubai (INR)', f'₹{converted["inr_equivalent"]:,.0f}')
            c2.metric('22K Dubai (AED)', f'AED {converted["aed_22k"]:,.0f}')
            c3.metric('USD/oz Int\'l', f'${converted["usd_per_oz"]:,.2f}')
        else:
            st.markdown(f'## 🏆 MCX Landed: ₹{converted["mcx_landed"]:,.0f}')
            c1, c2, c3 = st.columns(3)
            c1.metric('24K Retail (India)', f'₹{converted["retail_24k"]:,.0f}')
            c2.metric('22K Retail (India)', f'₹{converted["retail_22k"]:,.0f}')
            c3.metric('Intl USD/oz', f'${converted["usd_per_oz"]:,.2f}')
        st.caption('💡 Separate tickers for India MCX and Dubai Spot rates.')
# TABS
# ═══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🤖 AI & ML Analysis",
    "📰 News & Sentiment",
    "📐 Technicals",
    "🗂️ EDA Report",
])


# ─── TAB 1: DASHBOARD ────────────────────────────────────────
with tab1:
    # Candlestick
    fig_candle = charts.candlestick_chart(
        df, f"{selected_name} ({selected_ticker})", show_bb, show_ema, show_vol
    )
    st.plotly_chart(fig_candle, config={"displayModeBar": False})

    col_left, col_mid, col_right = st.columns([1.3, 1, 1.2])

    # Performance
    with col_left:
        st.markdown("**📈 Performance**")
        if perf:
            st.plotly_chart(charts.performance_chart(perf), config={"displayModeBar": False})
        else:
            st.info("Performance data unavailable.")

    # Technical Rating Gauge
    with col_mid:
        st.markdown("**⚡ Technical Rating**")
        osc_sum = get_oscillator_summary(df)
        ma_sum = get_ma_summary(df)
        rating_text, rating_score = get_overall_rating(osc_sum, ma_sum)
        gauge_score = (rating_score + 1) / 2
        st.plotly_chart(
            charts.signal_gauge(gauge_score, "Rating"),
            config={"displayModeBar": False},
        )
        ob, on, os_ = osc_sum[0], osc_sum[1], osc_sum[2]
        mb, mn, ms_ = ma_sum[0], ma_sum[1], ma_sum[2]
        r1, r2, r3 = st.columns(3)
        r1.metric("Buy", ob + mb)
        r2.metric("Neutral", on + mn)
        r3.metric("Sell", os_ + ms_)

    # Support / Resistance + Trade Plan
    with col_right:
        st.markdown("**🎯 Support & Resistance**")
        s2, s1, res1, res2 = get_support_resistance(df)
        price_now = float(df["Close"].iloc[-1]) if not df.empty else 0
        atr_val = float(df["ATR"].iloc[-1]) if "ATR" in df.columns and not pd.isna(df["ATR"].iloc[-1]) else price_now * 0.02

        if s2:
            st.markdown(f"""
| Level | Price |
|---|---|
| **Resistance 2** | {currency}{res2:,.2f} |
| **Resistance 1** | {currency}{res1:,.2f} |
| **▶ Current** | **{currency}{price_now:,.2f}** |
| **Support 1** | {currency}{s1:,.2f} |
| **Support 2** | {currency}{s2:,.2f} |
""")

        plan = get_trade_plan(
            {"signal": rating_text.upper(), "score": gauge_score},
            price_now, atr_val,
        )
        st.markdown("**📋 Trade Plan**")
        st.markdown(f"""
| | Price |
|---|---|
| Entry | {currency}{plan['entry']:,.2f} |
| Target 1 | {currency}{plan['target_1']:,.2f} |
| Target 2 | {currency}{plan['target_2']:,.2f} |
| Stop Loss | {currency}{plan['stop_loss']:,.2f} |
| R:R Ratio | {plan['risk_reward']:.2f}x |
""")


# ─── TAB 2: AI & ML ANALYSIS ────────────────────────────────
with tab2:
    st.markdown(f"### 🤖 AI Analysis — {selected_name}")
    st.caption("EDA runs first → best models selected automatically → full metrics reported")

    if st.button("🚀 Run Full AI Analysis", type="primary"):
        with st.spinner("Running EDA + training ML models... (30–60s)"):
            ml_data = get_ml_results(df)
            st.session_state["ml_data"] = ml_data
            st.session_state["ml_ticker"] = selected_ticker

    ml_data = st.session_state.get("ml_data")
    if not ml_data or st.session_state.get("ml_ticker") != selected_ticker:
        st.info("👆 Click **Run Full AI Analysis** to start.")
    else:
        eda = ml_data.get("eda", {})
        models = ml_data.get("models", {})
        ensemble = models.get("_ensemble", {})

        # ── EDA Summary ──
        st.markdown("#### 📋 EDA Summary")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Samples", eda.get("n_samples", "–"))
        e2.metric("Features", eda.get("n_features", "–"))
        e3.metric("Stationary", "✅" if eda.get("is_stationary") else "❌")
        e4.metric("Balanced", "✅" if eda.get("is_balanced") else "⚠️")

        m1, m2, m3, m4 = st.columns(4)
        rs = eda.get("return_stats", {})
        m1.metric("Skewness", rs.get("skewness", "–"))
        m2.metric("Kurtosis", rs.get("kurtosis", "–"))
        m3.metric("Autocorr", "⚡ Yes" if eda.get("has_autocorrelation") else "No")
        m4.metric("Volatility", eda.get("volatility_regime", "–").capitalize())

        # EDA Warnings
        for w in eda.get("warnings", []):
            st.warning(f"⚠️ {w}")

        rec = eda.get("recommended_models", [])
        st.success(f"**Models selected by EDA:** {', '.join(rec)}")
        st.divider()

        # ── Ensemble Result ──
        if ensemble:
            cons = ensemble.get("consensus", "–")
            color = "green" if cons == "UP" else ("red" if cons == "DOWN" else "orange")
            st.markdown(
                f"### Ensemble Consensus: :{color}[**{cons}**] "
                f"({ensemble.get('n_models', 0)} models)"
            )
            ec1, ec2, ec3 = st.columns(3)
            ec1.metric("Avg Prob UP", f"{ensemble.get('avg_prob_up', 0)*100:.1f}%")
            ec2.metric("Avg Accuracy", f"{ensemble.get('avg_accuracy', 0):.1f}%")
            ec3.metric("Best Model", f"{ensemble.get('best_model', '–')} (AUC: {ensemble.get('best_roc_auc', 0):.3f})")

        # ── Per-Model Metrics Table ──
        model_names = [k for k in models if not k.startswith("_")]
        if model_names:
            st.markdown("#### 📊 Model Metrics")

            # Comparison chart
            st.plotly_chart(
                charts.ml_comparison_chart(models),
                config={"displayModeBar": False},
            )

            # Detailed table
            rows = []
            for name in model_names:
                m = models[name]
                if "error" not in m:
                    rows.append({
                        "Model": name,
                        "Accuracy %": m.get("accuracy", 0),
                        "Precision %": m.get("precision", 0),
                        "Recall %": m.get("recall", 0),
                        "F1 %": m.get("f1_score", 0),
                        "ROC-AUC": m.get("roc_auc", 0),
                        "CV Acc %": f"{m.get('cv_accuracy_mean',0)} ± {m.get('cv_accuracy_std',0)}",
                        "CV AUC": m.get("cv_auc_mean", 0),
                        "Prob UP %": f"{m.get('prob_up',0)*100:.1f}",
                        "Signal": m.get("prediction", "–"),
                    })
            if rows:
                st.dataframe(pd.DataFrame(rows).set_index("Model"))

            # Confusion Matrices
            st.markdown("#### 🧮 Confusion Matrices")
            cm_cols = st.columns(min(len(model_names), 4))
            for i, name in enumerate(model_names[:4]):
                m = models[name]
                if "confusion_matrix" in m:
                    import plotly.figure_factory as ff
                    cm = m["confusion_matrix"]
                    fig_cm = ff.create_annotated_heatmap(
                        z=cm,
                        x=["Pred DOWN", "Pred UP"],
                        y=["Act DOWN", "Act UP"],
                        colorscale=[[0, "#0D1117"], [1, "#6C63FF"]],
                        annotation_text=[[str(v) for v in row] for row in cm],
                        showscale=False,
                    )
                    fig_cm.update_layout(
                        paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                        font=dict(color="#E6EDF3"), height=220,
                        margin=dict(l=5, r=5, t=30, b=5),
                        title=dict(text=name, font=dict(size=12)),
                    )
                    cm_cols[i].plotly_chart(fig_cm, config={"displayModeBar": False})

            # Feature Importance
            best_name = ensemble.get("best_model", model_names[0]) if ensemble else model_names[0]
            best_m = models.get(best_name, {})
            if best_m.get("feature_importance"):
                st.markdown(f"#### 🔑 Feature Importance — {best_name}")
                feat_names, feat_vals = zip(*best_m["feature_importance"])
                import plotly.graph_objects as go
                fi_fig = go.Figure(go.Bar(
                    y=list(feat_names), x=list(feat_vals),
                    orientation="h", marker_color="#6C63FF",
                    text=[f"{v:.3f}" for v in feat_vals], textposition="outside",
                ))
                fi_fig.update_layout(
                    paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                    font=dict(color="#E6EDF3"), height=320, showlegend=False,
                    margin=dict(l=10, r=60, t=10, b=10),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fi_fig, config={"displayModeBar": False})


# ─── TAB 3: NEWS & SENTIMENT ─────────────────────────────────
with tab3:
    st.markdown(f"### 📰 News & Sentiment — {selected_name}")

    market_type = "indian" if "🇮🇳" in selected_market else ("commodities" if "🪙" in selected_market else ("forex" if "💱" in selected_market else "us"))

    with st.spinner("Fetching news..."):
        ticker_articles = fetch_ticker_news(selected_ticker)
        market_articles = fetch_market_news(market_type)

    all_articles = ticker_articles + market_articles[:5]
    sentiment_score, sentiment_label, sentiment_counts = compute_sentiment_score(all_articles)

    col_news, col_sent = st.columns([2, 1])

    with col_news:
        st.markdown(f"**{len(all_articles)} articles found**")
        for art in all_articles[:15]:
            icon = "🟢" if art["sentiment_label"] == "Positive" else ("🔴" if art["sentiment_label"] == "Negative" else "🟡")
            st.markdown(f"{icon} **{art['title']}**")
            st.caption(f"{art.get('source', '?')} · Sentiment: {art['sentiment']:+.2f}")

    with col_sent:
        st.markdown("**Overall Sentiment**")
        sig_col = "green" if "Bullish" in sentiment_label else ("red" if "Bearish" in sentiment_label else "orange")
        st.markdown(f"### :{sig_col}[{sentiment_label}]")
        st.metric("Score", f"{sentiment_score:+.3f}")

        pos = sentiment_counts["positive"]
        neg = sentiment_counts["negative"]
        neu = sentiment_counts["neutral"]
        st.plotly_chart(
            charts.sentiment_donut(pos, neg, neu),
            config={"displayModeBar": False},
        )

        # Quick technicals sidebar
        if "RSI" in df.columns:
            st.markdown("**Key Indicators**")
            latest = df.iloc[-1]
            for label, col_name in [("RSI", "RSI"), ("MACD", "MACD"), ("CCI", "CCI"), ("ADX", "ADX")]:
                if col_name in latest and not pd.isna(latest[col_name]):
                    st.metric(label, f"{latest[col_name]:.2f}")


# ─── TAB 4: TECHNICAL INDICATORS ─────────────────────────────
with tab4:
    st.markdown(f"### 📐 Technical Indicators — {selected_name}")

    col_osc, col_ma = st.columns(2)
    osc_b, osc_n, osc_s, osc_details = get_oscillator_summary(df)
    ma_b, ma_n, ma_s, ma_details = get_ma_summary(df)

    with col_osc:
        st.markdown(f"**Oscillators** — 🟢 Buy: {osc_b} | 🟡 Neutral: {osc_n} | 🔴 Sell: {osc_s}")
        for label, value, signal in osc_details:
            icon = "🟢" if signal == "Buy" else ("🔴" if signal == "Sell" else "🟡")
            st.markdown(f"{icon} **{label}**: {value} → _{signal}_")

    with col_ma:
        st.markdown(f"**Moving Averages** — 🟢 Buy: {ma_b} | 🟡 Neutral: {ma_n} | 🔴 Sell: {ma_s}")
        for label, value, signal in ma_details:
            icon = "🟢" if signal == "Buy" else ("🔴" if signal == "Sell" else "🟡")
            st.markdown(f"{icon} **{label}**: {currency}{value:,.2f} → _{signal}_")

    st.divider()

    col_rsi, col_bb = st.columns(2)
    with col_rsi:
        st.plotly_chart(charts.rsi_chart(df), config={"displayModeBar": False})

    with col_bb:
        if "BB_Upper" in df.columns and "BB_Lower" in df.columns:
            import plotly.graph_objects as go
            df_bb = df.copy()
            df_bb["BB_pct"] = (df_bb["Close"] - df_bb["BB_Lower"]) / (df_bb["BB_Upper"] - df_bb["BB_Lower"])
            x = df_bb["Date"] if "Date" in df_bb.columns else df_bb.index
            bb_fig = go.Figure()
            bb_fig.add_hline(y=1.0, line_dash="dot", line_color="#FF4757", opacity=0.5)
            bb_fig.add_hline(y=0.0, line_dash="dot", line_color="#00C896", opacity=0.5)
            bb_fig.add_trace(go.Scatter(
                x=x, y=df_bb["BB_pct"], name="BB %B",
                line=dict(color="#6C63FF", width=2),
                fill="tozeroy", fillcolor="rgba(108,99,255,0.08)",
            ))
            bb_fig.update_layout(
                paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
                font=dict(color="#E6EDF3"), height=200,
                margin=dict(l=10, r=10, t=30, b=10),
                title=dict(text="Bollinger Band %B", font=dict(size=13)),
                showlegend=False,
            )
            st.plotly_chart(bb_fig, config={"displayModeBar": False})


# ─── TAB 5: EDA REPORT ───────────────────────────────────────
with tab5:
    st.markdown(f"### 🗂️ EDA Report — {selected_name}")

    ml_data = st.session_state.get("ml_data")
    if not ml_data:
        st.info("Run the **AI Analysis** tab first to see the full EDA report.")
    else:
        eda = ml_data.get("eda", {})

        st.markdown("#### Return Statistics")
        rs = eda.get("return_stats", {})
        if rs:
            r1, r2, r3, r4, r5 = st.columns(5)
            r1.metric("Mean Return", f"{rs.get('mean_return_pct', 0):.3f}%")
            r2.metric("Std Dev", f"{rs.get('std_pct', 0):.3f}%")
            r3.metric("Skewness", f"{rs.get('skewness', 0):.3f}")
            r4.metric("Kurtosis", f"{rs.get('kurtosis', 0):.3f}")
            r5.metric("Normal Dist", "✅" if rs.get("is_normal") else "❌")

        st.markdown("#### Stationarity & Autocorrelation")
        sa1, sa2, sa3, sa4 = st.columns(4)
        sa1.metric("ADF Stat", eda.get("adf_stat", "–"))
        sa2.metric("ADF p-value", eda.get("adf_p", "–"))
        sa3.metric("Stationary", "✅" if eda.get("is_stationary") else "❌")
        sa4.metric("Ljung-Box p", eda.get("ljungbox_p", "–"))

        st.markdown("#### Top Features by Mutual Information")
        tf = eda.get("top_features", [])
        if tf:
            import plotly.graph_objects as go
            feat_df = pd.DataFrame(tf, columns=["Feature", "MI Score"])
            fi2 = go.Figure(go.Bar(
                y=feat_df["Feature"], x=feat_df["MI Score"],
                orientation="h", marker_color="#00D2FF",
                text=[f"{v:.3f}" for v in feat_df["MI Score"]], textposition="outside",
            ))
            fi2.update_layout(
                paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                font=dict(color="#E6EDF3"), height=300, showlegend=False,
                margin=dict(l=10, r=60, t=10, b=10),
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fi2, config={"displayModeBar": False})

        st.markdown("#### EDA Insights")
        for w in eda.get("warnings", []):
            st.warning(f"⚠️ {w}")
        if not eda.get("warnings"):
            st.success("✅ No major data quality issues detected.")

        st.markdown("#### Model Selection Scoring")
        ms = eda.get("model_flags", {}).get("model_scores", {})
        if ms:
            st.dataframe(
                pd.DataFrame(ms.items(), columns=["Model", "Score"]).sort_values("Score", ascending=False)
            )


# ═══════════════════════════════════════════════════════════════
# AUTO REFRESH
# ═══════════════════════════════════════════════════════════════
if auto_refresh:
    st.caption(f"Auto-refreshing in {REFRESH_INTERVAL}s...")
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

# Footer
st.divider()
st.caption("TradeIntel Pro · Data: Yahoo Finance · Not financial advice · Educational use only")
