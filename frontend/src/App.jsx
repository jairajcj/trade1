import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Clock, Activity, Zap, Globe, Info, RefreshCw } from 'lucide-react';
import './App.css';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/dashboard`);
      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setError("Failed to connect to Intelligence Engine. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000); // Auto-refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <h2 style={{ color: '#38bdf8', letterSpacing: '2px' }}>INITIALIZING SUPER-INTELLIGENCE</h2>
        <p style={{ color: '#64748b' }}>Correlating global geopolitics with Nifty market data...</p>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="dashboard-header">
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 900, letterSpacing: '-0.5px' }}>
            QUANT<span style={{ color: '#38bdf8' }}>INTEL</span> DASHBOARD v3.0
          </h1>
          <p style={{ margin: 0, fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>
            AI-DRIVEN MARKET SUPERPOSITION ENGINE
          </p>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div className={`market-status-pill ${data?.is_open ? 'status-open' : 'status-closed'}`}>
            <Clock size={14} />
            {data?.market_status || "Checking Market..."}
          </div>
          <button className="market-status-pill" style={{ cursor: 'pointer', background: 'rgba(255,255,255,0.05)' }} onClick={fetchDashboard}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            REFRESH
          </button>
        </div>
      </header>

      <div className="dashboard-grid">
        {/* Left Panel: Top Picks & Intelligence */}
        <div className="panel">
          <div className="panel-title">
            <Zap size={20} />
            TOP 5 HIGH-MARGIN INVESTMENT PICKS
          </div>

          <div className="picks-list">
            {data?.top_5?.map((stock, idx) => (
              <motion.div
                key={stock.ticker}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="pick-card"
              >
                <div className="card-header">
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
                    <span className="ticker-box">{stock.ticker}</span>
                    <span className={`signal-badge ${stock.signal === 'BUY' ? 'signal-buy' : stock.signal === 'SELL' ? 'signal-sell' : 'signal-hold'}`} style={{ fontSize: '0.65rem', padding: '1px 8px', borderRadius: '4px' }}>
                      {stock.signal}
                    </span>
                  </div>
                  <div className="superposition-badge">
                    SUPERPOSITION: {(stock.superposition * 100).toFixed(1)}%
                  </div>
                </div>

                <div className="card-stats">
                  <div className="stat-group">
                    <span className="stat-label">Current Price</span>
                    <span className="stat-val">₹{stock.price}</span>
                  </div>
                  <div className="stat-group">
                    <span className="stat-label">7D Trend</span>
                    <span className={`stat-val ${stock.trend_past_7d >= 0 ? 'trend-up' : 'trend-down'}`}>
                      {stock.trend_past_7d >= 0 ? '+' : ''}{stock.trend_past_7d}%
                    </span>
                  </div>
                  <div className="stat-group">
                    <span className="stat-label">UP Probability</span>
                    <span className="stat-val" style={{ color: '#38bdf8' }}>{(stock.probability * 100).toFixed(1)}%</span>
                  </div>
                </div>

                <div className="news-pulse">
                  <div className="stat-label" style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Globe size={10} /> GEOPOLITICAL NEWS PULSE
                  </div>
                  {stock.news_sample.map((n, i) => (
                    <div key={i} className="news-item">
                      <span style={{ color: '#38bdf8' }}>•</span>
                      {n.length > 80 ? n.substring(0, 80) + '...' : n}
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Right Panel: Market Context */}
        <div className="panel">
          <div className="panel-title">
            <Activity size={20} />
            GLOBAL CONTEXT ENGINE
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.3)', borderRadius: '12px', padding: '20px', flexGrow: 1 }}>
            <h3 style={{ fontSize: '0.9rem', color: '#64748b', marginTop: 0 }}>INTELLIGENCE SUMMARY</h3>
            <p style={{ fontSize: '0.85rem', lineHeight: 1.6, color: '#94a3b8' }}>
              The system is currently correlating <strong>India Stock Market</strong> trends with <strong>Global Geopolitics</strong>.
              {data?.is_open ?
                " Live signals are being generated based on real-time price action and news flow." :
                " Market is currently closed. Displaying predictive signals for the next opening session based on overnight global news."
              }
            </p>

            <div style={{ marginTop: '24px' }}>
              <div className="stat-label" style={{ marginBottom: '12px' }}>CONNECTION FACTORS</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <FactorBar label="AI Quantitative Prediction" value={85} color="#38bdf8" />
                <FactorBar label="News Sentiment Analysis" value={70} color="#818cf8" />
                <FactorBar label="Volume Anomaly Factor" value={45} color="#c084fc" />
              </div>
            </div>

            <div style={{ marginTop: 'auto', paddingTop: '24px', borderTop: '1px solid rgba(255,255,255,0.05)', textAlign: 'center' }}>
              <Info size={16} color="#64748b" style={{ margin: '0 auto 8px' }} />
              <p style={{ fontSize: '0.65rem', color: '#475569', fontWeight: 600 }}>
                DISCLAIMER: This is an AI-driven analytical dashboard. Always consult a financial advisor before making investment decisions.
              </p>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div style={{ position: 'fixed', bottom: '24px', right: '24px', background: '#ef4444', color: 'white', padding: '12px 24px', borderRadius: '8px', fontWeight: 700, boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)' }}>
          {error}
        </div>
      )}
    </div>
  );
}

function FactorBar({ label, value, color }) {
  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', marginBottom: '4px' }}>
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          style={{ height: '100%', background: color }}
        />
      </div>
    </div>
  );
}

export default App;
