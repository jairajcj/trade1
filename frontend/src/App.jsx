import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Clock, Activity, Zap, Globe, Info, RefreshCw, Radio, Search } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import './App.css';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchDashboard = async (force = false) => {
    try {
      const url = `http://localhost:8000/dashboard${force ? '?refresh=true' : ''}`;
      const response = await fetch(url);
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
    fetchDashboard(false); // Initial load (cached is fine)
    const interval = setInterval(() => fetchDashboard(true), 2000); // Live refresh every 2s
    return () => clearInterval(interval);
  }, []);

  const filteredPicks = data?.top_picks?.filter(stock =>
    stock.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
    stock.signal.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  if (loading && !data) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <h2 style={{ color: '#38bdf8', letterSpacing: '2px' }}>INITIALIZING SUPER-INTELLIGENCE</h2>
        <p style={{ color: '#64748b' }}>Correlating global geopolitics with NSE Growth Market data...</p>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="dashboard-header">
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 900, letterSpacing: '-0.5px' }}>
            NSE<span style={{ color: '#38bdf8' }}>INTEL</span> GROWTH SCANNER
          </h1>
          <p style={{ margin: 0, fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>
            NSE-SPECIFIC AI GROWTH SUPERPOSITION ENGINE
          </p>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div className="market-status-pill live-indicator">
            <Radio size={14} className="pulse" />
            LIVE ANALYSIS
          </div>
          <div className={`market-status-pill ${data?.is_open ? 'status-open' : 'status-closed'}`}>
            <Clock size={14} />
            {data?.market_status || "Checking Market..."}
          </div>
          <button className="market-status-pill" style={{ cursor: 'pointer', background: 'rgba(255,255,255,0.05)' }} onClick={() => fetchDashboard(true)}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            REFRESH
          </button>
        </div>
      </header>

      <div className="dashboard-grid">
        {/* Left Panel: Full-Market Scanner */}
        <div className="panel">
          <div className="panel-title" style={{ justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Zap size={20} />
              NSE FULL-MARKET GROWTH SCANNER
            </div>
            <div className="results-count">
              {filteredPicks.length} ASSETS MATCHING
            </div>
          </div>

          <div className="search-container">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder="Search ticker, signal (BUY/HOLD), or triggers..."
              className="search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="picks-list">
            {filteredPicks.length > 0 ? (
              filteredPicks.map((stock, idx) => (
                <motion.div
                  key={stock.ticker}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(idx * 0.05, 0.5) }}
                  className={`pick-card ${stock.signal === 'BUY' ? 'pick-buy' : stock.signal === 'SELL' ? 'pick-sell' : ''}`}
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

                  <div className="card-content-grid">
                    <div className="card-stats">
                      <div className="stat-group">
                        <span className="stat-label">Price</span>
                        <span className="stat-val">₹{stock.price}</span>
                      </div>
                      <div className="stat-group">
                        <span className="stat-label">7D Trend</span>
                        <span className={`stat-val ${stock.trend_past_7d >= 0 ? 'trend-up' : 'trend-down'}`}>
                          {stock.trend_past_7d >= 0 ? '+' : ''}{stock.trend_past_7d}%
                        </span>
                      </div>
                      <div className="stat-group">
                        <span className="stat-label">UP Prob</span>
                        <span className="stat-val" style={{ color: '#38bdf8' }}>{(stock.probability * 100).toFixed(1)}%</span>
                      </div>
                    </div>

                    <div className="mini-chart">
                      <ResponsiveContainer width="100%" height={60}>
                        <LineChart data={stock.history}>
                          <Line
                            type="monotone"
                            dataKey="price"
                            stroke={stock.trend_past_7d >= 0 ? "#4ade80" : "#f87171"}
                            strokeWidth={2}
                            dot={false}
                          />
                          <Tooltip
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                return (
                                  <div className="custom-tooltip">
                                    ₹{payload[0].value}
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="strategy-section">
                    <div className="strategy-labels">
                      <div className="strategy-stat">
                        <span className="strat-label">{stock.signal === 'BUY' ? 'ENTRY ABOVE' : 'SELL BELOW'}</span>
                        <span className="strat-val">₹{stock.buy_above}</span>
                      </div>
                      <div className="strategy-stat">
                        <span className="strat-label">TARGET</span>
                        <span className="strat-val" style={{ color: '#4ade80' }}>₹{stock.target}</span>
                      </div>
                      <div className="strategy-stat">
                        <span className="strat-label">STOP LOSS</span>
                        <span className="strat-val" style={{ color: '#f87171' }}>₹{stock.stop_loss}</span>
                      </div>
                    </div>
                    <div className="trigger-cloud">
                      {stock.triggers.map((t, i) => (
                        <span key={i} className="trigger-chip">{t}</span>
                      ))}
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
              ))
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                No assets found matching your search criteria.
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Market Context */}
        <div className="panel">
          <div className="panel-title">
            <Activity size={20} />
            NSE MARKET CONTEXT
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.3)', borderRadius: '12px', padding: '20px', flexGrow: 1 }}>
            <h3 style={{ fontSize: '0.9rem', color: '#64748b', marginTop: 0 }}>INTELLIGENCE SUMMARY</h3>
            <p style={{ fontSize: '0.85rem', lineHeight: 1.6, color: '#94a3b8' }}>
              The system is currently correlating <strong>NSE (National Stock Exchange)</strong> growth trends with <strong>Global Geopolitics</strong>.
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
