import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ReportForm from './components/ReportForm';
import DefectMap from './components/DefectMap';
import AdminPortal from './components/AdminPortal';
import ModelTelemetry from './components/ModelTelemetry';

export default function App() {
  const [activeTab, setActiveTab] = useState('report'); // 'report' | 'map' | 'telemetry' | 'admin'
  const [adminToken, setAdminToken] = useState(() => localStorage.getItem('civic_admin_token') || null);
  const [adminUser, setAdminUser] = useState(() => {
    try {
      const saved = localStorage.getItem('civic_admin_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const handleLoginSuccess = (token, userData) => {
    setAdminToken(token);
    setAdminUser(userData);
    localStorage.setItem('civic_admin_token', token);
    localStorage.setItem('civic_admin_user', JSON.stringify(userData));
    setActiveTab('admin');
  };

  const handleLogout = () => {
    setAdminToken(null);
    setAdminUser(null);
    localStorage.removeItem('civic_admin_token');
    localStorage.removeItem('civic_admin_user');
    setActiveTab('report');
  };

  const handleReportSubmitted = (newReport) => {
    console.log('New verified report received:', newReport);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div className="bg-mesh"></div>

      {/* Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        adminUser={adminUser}
        onLogout={handleLogout}
        onOpenLogin={() => setActiveTab('admin')}
      />

      {/* Main Views */}
      <main style={{ flex: 1 }}>
        {activeTab === 'report' && (
          <ReportForm onReportSubmitted={handleReportSubmitted} />
        )}

        {activeTab === 'map' && (
          <DefectMap onSelectReport={(r) => {
            console.log('Selected report from map:', r);
            setActiveTab('admin');
          }} />
        )}

        {activeTab === 'telemetry' && (
          <ModelTelemetry adminToken={adminToken} />
        )}

        {activeTab === 'admin' && (
          <AdminPortal
            adminToken={adminToken}
            onLoginSuccess={handleLoginSuccess}
          />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        padding: '24px 16px',
        textAlign: 'center',
        background: 'rgba(10, 15, 29, 0.95)',
        fontSize: '12px',
        color: 'var(--text-muted)'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            CivicWatch Intelligent Road Infrastructure Platform &bull; PyTorch ResNet-50 CV Model (v1)
          </div>
          <div style={{ display: 'flex', gap: '16px' }}>
            <span>Zero Data Leakage Pipeline</span>
            <span>Grad-CAM Explainability</span>
            <span>FastAPI + PostgreSQL Ready</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
