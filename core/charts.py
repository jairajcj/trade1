"""
TradeIntel Pro - Chart Builder
Plotly TradingView-style charts.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

DARK_THEME = dict(
    plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
    font=dict(color="#E6EDF3", family="Inter, sans-serif"),
    margin=dict(l=10, r=10, t=40, b=10),
)

def _apply_dark(fig, title="", height=400):
    fig.update_layout(**DARK_THEME, height=height,
        title=dict(text=title, font=dict(size=14, color="#8B949E"), x=0.02),
        legend=dict(bgcolor="#161B22", bordercolor="#30363D", borderwidth=1),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#1C2128", linecolor="#30363D", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#1C2128", linecolor="#30363D", zeroline=False)
    return fig


def candlestick_chart(df, ticker_name="", show_bb=True, show_ema=True, show_volume=True):
    """Full candlestick with Bollinger Bands, EMA, MACD, Volume subplots."""
    if df.empty or len(df) < 5:
        return go.Figure()

    rows = 3 if show_volume else 2
    row_heights = [0.60, 0.20, 0.20] if show_volume else [0.70, 0.30]
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
        vertical_spacing=0.02, row_heights=row_heights)

    x = df['Date'] if 'Date' in df.columns else df.index

    # Candlestick
    fig.add_trace(go.Candlestick(x=x, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        increasing_line_color='#00C896', decreasing_line_color='#FF4757',
        increasing_fillcolor='#00C896', decreasing_fillcolor='#FF4757',
        name="Price"), row=1, col=1)

    # Bollinger Bands
    if show_bb and 'BB_Upper' in df.columns:
        fig.add_trace(go.Scatter(x=x, y=df['BB_Upper'], name="BB Upper",
            line=dict(color="#6C63FF", width=1, dash="dot"), opacity=0.6), row=1, col=1)
        fig.add_trace(go.Scatter(x=x, y=df['BB_Lower'], name="BB Lower",
            line=dict(color="#6C63FF", width=1, dash="dot"), opacity=0.6,
            fill='tonexty', fillcolor='rgba(108,99,255,0.05)'), row=1, col=1)

    # EMAs
    if show_ema:
        if 'EMA_12' in df.columns:
            fig.add_trace(go.Scatter(x=x, y=df['EMA_12'], name="EMA 12",
                line=dict(color="#FFD700", width=1.5)), row=1, col=1)
        if 'SMA_50' in df.columns:
            fig.add_trace(go.Scatter(x=x, y=df['SMA_50'], name="SMA 50",
                line=dict(color="#00D2FF", width=1.5, dash="dot")), row=1, col=1)

    # MACD
    if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
        hist_colors = ['#00C896' if v >= 0 else '#FF4757' for v in df.get('MACD_Hist', pd.Series([0]*len(df))).fillna(0)]
        fig.add_trace(go.Bar(x=x, y=df.get('MACD_Hist', pd.Series([0]*len(df))),
            name="Hist", marker_color=hist_colors, opacity=0.6), row=2, col=1)
        fig.add_trace(go.Scatter(x=x, y=df['MACD'], name="MACD",
            line=dict(color="#6C63FF", width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=x, y=df['MACD_Signal'], name="Signal",
            line=dict(color="#FF6B35", width=1.5)), row=2, col=1)

    # Volume
    if show_volume and 'Volume' in df.columns:
        vol_colors = ['#00C896' if c >= o else '#FF4757' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=x, y=df['Volume'], name="Volume",
            marker_color=vol_colors, opacity=0.5), row=3, col=1)

    fig.update_layout(**DARK_THEME, height=560, xaxis_rangeslider_visible=False,
        title=dict(text=f"{ticker_name} — Price Chart", font=dict(size=15, color="#E6EDF3"), x=0.02),
        legend=dict(bgcolor="#161B22", bordercolor="#30363D", borderwidth=1,
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(showgrid=True, gridcolor="#1C2128", linecolor="#30363D")
    fig.update_yaxes(showgrid=True, gridcolor="#1C2128", linecolor="#30363D")
    return fig


def signal_gauge(score, title="Signal"):
    """Semicircle signal gauge (score: 0 to 1)."""
    value = round((score - 0.5) * 200, 1)
    if value > 50:   color, label = "#00C896", ("Strong Buy" if value > 75 else "Buy")
    elif value < -50: color, label = "#FF4757", ("Strong Sell" if value < -75 else "Sell")
    else:             color, label = "#FFA502", "Neutral"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": f"<b>{label}</b>", "font": {"size": 16, "color": color}},
        gauge={
            "axis": {"range": [-100, 100], "tickvals": [-100, -50, 0, 50, 100],
                     "ticktext": ["St.Sell", "Sell", "Neutral", "Buy", "St.Buy"],
                     "tickfont": {"size": 9, "color": "#8B949E"}, "tickwidth": 1, "tickcolor": "#30363D"},
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": "#161B22", "borderwidth": 0,
            "steps": [
                {"range": [-100, -50], "color": "#3D1520"},
                {"range": [-50,  0],  "color": "#2D1F0F"},
                {"range": [0,   50],  "color": "#0F2D1F"},
                {"range": [50, 100],  "color": "#0F3020"},
            ],
        },
        number={"font": {"size": 20, "color": color}},
    ))
    fig.update_layout(paper_bgcolor="#161B22", plot_bgcolor="#161B22",
        font=dict(color="#E6EDF3"), height=200, margin=dict(l=20, r=20, t=40, b=10))
    return fig


def rsi_chart(df):
    """RSI with overbought/oversold zones."""
    if df.empty or 'RSI' not in df.columns:
        return go.Figure()
    x = df['Date'] if 'Date' in df.columns else df.index
    fig = go.Figure()
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255,71,87,0.15)", line_width=0)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,200,150,0.15)", line_width=0)
    fig.add_hline(y=70, line_dash="dot", line_color="#FF4757", opacity=0.5)
    fig.add_hline(y=30, line_dash="dot", line_color="#00C896", opacity=0.5)
    fig.add_hline(y=50, line_dash="dot", line_color="#8B949E", opacity=0.3)
    fig.add_trace(go.Scatter(x=x, y=df['RSI'], name="RSI (14)",
        line=dict(color="#6C63FF", width=2),
        fill='tozeroy', fillcolor='rgba(108,99,255,0.08)'))
    return _apply_dark(fig, "RSI (14)", height=200)


def performance_chart(perf_dict):
    """Colored bar chart for multi-timeframe performance."""
    if not perf_dict:
        return go.Figure()
    labels, values = list(perf_dict.keys()), list(perf_dict.values())
    colors = ['#00C896' if v >= 0 else '#FF4757' for v in values]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors,
        text=[f"{v:+.2f}%" for v in values], textposition='outside',
        textfont=dict(size=11, color="#E6EDF3")))
    fig.update_layout(**DARK_THEME, height=220, showlegend=False,
        yaxis=dict(ticksuffix="%"),
        title=dict(text="Performance", font=dict(size=13, color="#8B949E"), x=0.02))
    return fig


def ml_comparison_chart(ml_results):
    """Side-by-side ML accuracy and probability bars."""
    if not ml_results:
        return go.Figure()
    models = [k for k in ml_results if not k.startswith("_")]
    accs   = [ml_results[m].get("accuracy", 0) for m in models]
    probs  = [ml_results[m].get("prob_up", 0.5) * 100 for m in models]
    colors = ['#00C896' if ml_results[m].get("prediction") == "UP" else '#FF4757' for m in models]

    fig = make_subplots(rows=1, cols=2,
        subplot_titles=("Model Accuracy (%)", "Prob UP (%)"))
    fig.add_trace(go.Bar(x=models, y=accs, name="Accuracy", marker_color="#6C63FF",
        text=[f"{v:.1f}%" for v in accs], textposition='outside'), row=1, col=1)
    fig.add_trace(go.Bar(x=models, y=probs, name="Prob UP", marker_color=colors,
        text=[f"{v:.1f}%" for v in probs], textposition='outside'), row=1, col=2)
    fig.update_layout(**DARK_THEME, height=280, showlegend=False,
        title=dict(text="ML Model Comparison", font=dict(size=13, color="#8B949E"), x=0.02))
    return fig


def sentiment_donut(pos, neg, neu, title="News Sentiment"):
    """Sentiment breakdown donut."""
    total = pos + neg + neu or 1
    fig = go.Figure(go.Pie(values=[pos, neg, neu],
        labels=["Positive", "Negative", "Neutral"],
        hole=0.65, marker_colors=["#00C896", "#FF4757", "#FFA502"],
        textinfo="percent+label", textfont=dict(size=10),
        hoverinfo="label+value+percent"))
    fig.update_layout(paper_bgcolor="#161B22", plot_bgcolor="#161B22",
        font=dict(color="#E6EDF3"), height=250,
        margin=dict(l=10, r=10, t=40, b=10),
        title=dict(text=title, font=dict(size=13, color="#8B949E"), x=0.02),
        legend=dict(bgcolor="#161B22", orientation="h", y=-0.1),
        annotations=[dict(text=f"{total}<br>Articles", x=0.5, y=0.5,
                         font_size=11, font_color="#8B949E", showarrow=False)])
    return fig
