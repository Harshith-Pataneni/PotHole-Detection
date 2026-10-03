import React, { useState } from 'react';
import Navbar from './components/Navbar';
import ReportForm from './components/ReportForm';
import DefectMap from './components/DefectMap';
import AdminPortal from './components/AdminPortal';
import ModelTelemetry from './components/ModelTelemetry';

export default function App() {
  const [viewMode, setViewMode] = useState('citizen'); // 'citizen' | 'admin'
  const [activeTab, setActiveTab] = useState('report'); // Citizen: 'report' | 'map'  Admin: 'admin' | 'map' | 'telemetry'
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
    setViewMode('admin');
    setActiveTab('admin');
  };

  const handleLogout = () => {
    setAdminToken(null);
    setAdminUser(null);
    localStorage.removeItem('civic_admin_token');
    localStorage.removeItem('civic_admin_user');
    setViewMode('citizen');
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
        viewMode={viewMode}
        setViewMode={setViewMode}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        adminUser={adminUser}
        onLogout={handleLogout}
      />

      {/* Main Views */}
      <main style={{ flex: 1 }}>
        {/* CITIZEN VIEWS */}
        {viewMode === 'citizen' && (
          <>
            {activeTab === 'report' && (
              <ReportForm onReportSubmitted={handleReportSubmitted} />
            )}
            {activeTab === 'map' && (
              <DefectMap onSelectReport={(r) => {
                console.log('Selected report from citizen map:', r);
              }} />
            )}
          </>
        )}

        {/* ADMIN VIEWS */}
        {viewMode === 'admin' && (
          <>
            {activeTab === 'admin' && (
              <AdminPortal
                adminToken={adminToken}
                onLoginSuccess={handleLoginSuccess}
              />
            )}

            {activeTab === 'map' && (
              <DefectMap onSelectReport={(r) => {
                console.log('Selected report from admin map:', r);
                setActiveTab('admin');
              }} />
            )}

            {activeTab === 'telemetry' && (
              <ModelTelemetry adminToken={adminToken} />
            )}
          </>
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
            <span>Smart Redundancy Shield</span>
            <span>Grad-CAM Explainability</span>
            <span>Resend Alerts Integrated</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
