import React, { useState, useEffect } from 'react';
import { Brain, RefreshCw, Crosshair, Users, Activity, Target, ShieldAlert } from 'lucide-react';
import './App.css';

const MLDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState("");
  const [recommendations, setRecommendations] = useState(null);

  useEffect(() => {
    fetchCustomers();
  }, []);

  const fetchCustomers = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/models/customers');
      const data = await res.json();
      setCustomers(data.customers || []);
    } catch (err) {
      console.error("Failed to fetch customers:", err);
    }
  };

  const handleTrainModels = async (endpoint, actionName) => {
    setLoading(true);
    setStatusMsg(`Running ${actionName}...`);
    try {
      const res = await fetch(`http://localhost:8000/api/models/${endpoint}`, { method: 'POST' });
      const data = await res.json();
      setStatusMsg(data.message || "Success!");
      // Automatically refresh the dropdown list in case Compile Feature Store just ran
      if (endpoint.includes('calculate-features') || endpoint === 'predict') {
          await fetchCustomers();
      }
    } catch (err) {
      setStatusMsg(`Error: ${err.message}`);
    }
    setLoading(false);
  };

  const handleFetchRecommendations = async (customerId) => {
    if (!customerId) return;
    setSelectedCustomer(customerId);
    setRecommendations(null);
    try {
      const res = await fetch(`http://localhost:8000/api/models/recommendations/${customerId}`);
      const data = await res.json();
      setRecommendations(data);
    } catch (err) {
      console.error("Failed to fetch recommendations:", err);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'CRITICAL': return '#EF4444'; // Red
      case 'HIGH': return '#F59E0B'; // Orange
      case 'MEDIUM': return '#3B82F6'; // Blue
      default: return '#10B981'; // Green
    }
  };

  return (
    <div className="ml-dashboard-container">
      <header className="ml-header">
        <h2><Brain className="inline-icon" /> AI & Recommendations Engine</h2>
        <p>Train models, predict churn, and generate CRM strategies.</p>
      </header>

      {/* Control Panel */}
      <div className="ml-control-panel">
        <h3>1. Engine Controls</h3>
        <div className="control-buttons">
          <button 
            onClick={() => handleTrainModels('../ml/calculate-features', 'Feature Engineering Compilation')}
            disabled={loading}
            className="btn-secondary"
            style={{ borderColor: '#4F46E5', color: '#4F46E5' }}
          >
            <Activity size={18} /> Compile Feature Store
          </button>

          <button 
            onClick={() => handleTrainModels('train-segmentation', 'Segmentation Training')}
            disabled={loading}
            className="btn-primary"
          >
            <Users size={18} /> Train Customer Segments
          </button>
          
          <button 
            onClick={() => handleTrainModels('train-churn', 'XGBoost Training')}
            disabled={loading}
            className="btn-primary"
          >
            <Target size={18} /> Train Churn Model
          </button>
          
          <button 
            onClick={() => handleTrainModels('predict', 'Inference Engine')}
            disabled={loading}
            className="btn-secondary"
          >
            <RefreshCw size={18} /> Generate New Predictions
          </button>
        </div>
        
        {statusMsg && (
          <div className={`status-banner ${loading ? 'pulsing' : ''}`}>
            {statusMsg}
          </div>
        )}
      </div>

      {/* Customer Insights */}
      <div className="ml-insights-panel">
        <h3>2. Customer Intelligence</h3>
        
        <div className="customer-selector">
          <label>Select Customer Profile:</label>
          <select 
            value={selectedCustomer} 
            onChange={(e) => handleFetchRecommendations(e.target.value)}
          >
            <option value="">-- Choose a Customer --</option>
            {customers.map(c => (
              <option key={c} value={c}>{c.toUpperCase()}</option>
            ))}
          </select>
        </div>

        {recommendations && (
          <div className="recommendations-display">
            <div className="rec-header">
              <h4>Profile: {recommendations.customer_id.toUpperCase()}</h4>
              <span className="segment-badge">{recommendations.segment || 'Unknown'}</span>
            </div>

            <div className="score-cards">
              <div className="score-card">
                <div className="score-title"><Activity size={16} /> Health Score</div>
                <div className="score-value">
                  {recommendations.health_score} <span>/ 100</span>
                </div>
                <div className="progress-bar-bg">
                  <div 
                    className="progress-bar-fill green" 
                    style={{ width: `${Math.min(100, Math.max(0, recommendations.health_score))}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="score-card">
                <div className="score-title"><Crosshair size={16} /> Churn Risk</div>
                <div className="score-value">
                  {recommendations.ml_churn_probability}%
                </div>
                <div className="progress-bar-bg">
                  <div 
                    className="progress-bar-fill red" 
                    style={{ width: `${Math.min(100, Math.max(0, recommendations.ml_churn_probability))}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="action-list">
              <h4>Recommended Business Actions:</h4>
              {recommendations.recommendations.map((rec, idx) => (
                <div key={idx} className="action-item" style={{ borderLeftColor: getPriorityColor(rec.priority) }}>
                  <div className="action-priority" style={{ color: getPriorityColor(rec.priority) }}>
                    <ShieldAlert size={14} /> {rec.priority} PRIORITY
                  </div>
                  <div className="action-text">{rec.action}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MLDashboard;
