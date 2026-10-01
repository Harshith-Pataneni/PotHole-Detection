import React from 'react';
import { Shield, MapPin, BarChart3, Lock, LogOut, Activity } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, adminUser, onLogout, onOpenLogin }) {
  return (
    <header style={{
      background: 'rgba(10, 15, 29, 0.85)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-subtle)',
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      padding: '0 24px'
    }}>
      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        height: '70px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        {/* Brand */}
        <div 
          onClick={() => setActiveTab('report')}
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        >
          <div style={{
            background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(59, 130, 246, 0.4)'
          }}>
            <Shield size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '19px', fontWeight: 800, letterSpacing: '-0.02em', color: '#ffffff', fontFamily: 'var(--font-heading)' }}>
                CivicWatch
              </span>
              <span style={{
                background: 'rgba(59, 130, 246, 0.15)',
                color: '#60a5fa',
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: '4px',
                border: '1px solid rgba(59, 130, 246, 0.3)'
              }}>
                CV-v1
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Intelligent Road Infrastructure Platform
            </div>
          </div>
        </div>

        {/* Nav Links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setActiveTab('report')}
            className={`btn ${activeTab === 'report' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 16px', fontSize: '13px' }}
          >
            <Shield size={16} />
            Report Defect
          </button>

          <button
            onClick={() => setActiveTab('map')}
            className={`btn ${activeTab === 'map' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 16px', fontSize: '13px' }}
          >
            <MapPin size={16} />
            Live Map
          </button>

          <button
            onClick={() => setActiveTab('telemetry')}
            className={`btn ${activeTab === 'telemetry' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 16px', fontSize: '13px' }}
          >
            <Activity size={16} />
            ML Telemetry
          </button>

          <button
            onClick={() => setActiveTab('admin')}
            className={`btn ${activeTab === 'admin' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 16px', fontSize: '13px' }}
          >
            <BarChart3 size={16} />
            Operations Portal
          </button>
        </nav>

        {/* User / Auth State */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {adminUser ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {adminUser.user_name || adminUser.user_email}
                </div>
                <div style={{ fontSize: '10px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
                  <span className="pulse-dot" style={{ width: '6px', height: '6px' }}></span>
                  Admin Authenticated
                </div>
              </div>
              <button
                onClick={onLogout}
                className="btn btn-secondary"
                style={{ padding: '6px 10px', borderRadius: '8px' }}
                title="Log Out"
              >
                <LogOut size={15} />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenLogin}
              className="btn btn-secondary"
              style={{ fontSize: '12px', padding: '7px 14px' }}
            >
              <Lock size={14} />
              Admin Access
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
