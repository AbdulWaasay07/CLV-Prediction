import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart 
} from 'recharts';
import { Users, DollarSign, TrendingUp, Activity } from 'lucide-react';
import './App.css';

const Dashboard = () => {
  const [kpis, setKpis] = useState(null);
  const [revenueTrends, setRevenueTrends] = useState([]);
  const [locations, setLocations] = useState([]);
  const [marketing, setMarketing] = useState([]);
  const [support, setSupport] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [kpiRes, revRes, locRes, mktRes, supRes] = await Promise.all([
          fetch('http://localhost:8000/api/eda/kpis'),
          fetch('http://localhost:8000/api/eda/revenue-trends'),
          fetch('http://localhost:8000/api/eda/customer-locations'),
          fetch('http://localhost:8000/api/eda/marketing-clv'),
          fetch('http://localhost:8000/api/eda/support-csat')
        ]);

        setKpis(await kpiRes.json());
        setRevenueTrends(await revRes.json());
        setLocations(await locRes.json());
        setMarketing(await mktRes.json());
        setSupport(await supRes.json());
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) return <div className="loading">Loading Dashboard...</div>;

  return (
    <div className="dashboard-container">
      <h2 className="dashboard-title">Executive Summary Dashboard</h2>
      
      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon-wrapper blue"><Users size={24} /></div>
          <div className="kpi-details">
            <p className="kpi-label">Total Customers</p>
            <h3 className="kpi-value">{kpis?.total_customers || 0}</h3>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon-wrapper green"><DollarSign size={24} /></div>
          <div className="kpi-details">
            <p className="kpi-label">Total Revenue</p>
            <h3 className="kpi-value">${kpis?.total_revenue?.toLocaleString() || 0}</h3>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon-wrapper purple"><TrendingUp size={24} /></div>
          <div className="kpi-details">
            <p className="kpi-label">30-Day MRR</p>
            <h3 className="kpi-value">${kpis?.total_mrr?.toLocaleString() || 0}</h3>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon-wrapper orange"><Activity size={24} /></div>
          <div className="kpi-details">
            <p className="kpi-label">Historic CLV</p>
            <h3 className="kpi-value">${kpis?.historic_clv?.toLocaleString() || 0}</h3>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        
        {/* Revenue Trends */}
        <div className="chart-card">
          <h3>Daily Revenue Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={revenueTrends}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="date" stroke="#6B7280" fontSize={12} tickLine={false} />
              <YAxis stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `$${value}`} />
              <Tooltip formatter={(value) => [`$${value}`, "Revenue"]} />
              <Line type="monotone" dataKey="revenue" stroke="#4F46E5" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 8 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Marketing CLV */}
        <div className="chart-card">
          <h3>Marketing Channel ROI (Avg Spend)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={marketing}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="channel" stroke="#6B7280" fontSize={12} tickLine={false} />
              <YAxis stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `$${value}`} />
              <Tooltip formatter={(value) => [`$${value}`, "Avg Spend"]} />
              <Bar dataKey="avg_spend" fill="#10B981" radius={[4, 4, 0, 0]} barSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Customer Locations */}
        <div className="chart-card">
          <h3>Customer Density by Location</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={locations} layout="vertical" margin={{ left: 30 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E5E7EB" />
              <XAxis type="number" stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis dataKey="location" type="category" stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey="density" fill="#6366F1" radius={[0, 4, 4, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Support CSAT vs Volume */}
        <div className="chart-card">
          <h3>Support Ticket CSAT vs Volume</h3>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={support}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="severity" stroke="#6B7280" fontSize={12} tickLine={false} />
              <YAxis yAxisId="left" stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis yAxisId="right" orientation="right" domain={[0, 5]} stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="volume" fill="#F59E0B" name="Ticket Volume" radius={[4, 4, 0, 0]} barSize={40} />
              <Line yAxisId="right" type="monotone" dataKey="avg_csat" stroke="#EF4444" strokeWidth={3} name="Avg CSAT Score" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
