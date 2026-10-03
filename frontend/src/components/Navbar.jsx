import React from 'react';
import { Shield, MapPin, BarChart3, Lock, LogOut, Activity, ArrowRight, Eye } from 'lucide-react';

export default function Navbar({ 
  viewMode, 
  setViewMode, 
  activeTab, 
  setActiveTab, 
  adminUser, 
  onLogout 
}) {
  const isAdmin = viewMode === 'admin';

  return (
    <header style={{
      background: isAdmin ? 'rgba(15, 23, 42, 0.95)' : 'rgba(10, 15, 29, 0.85)',
      backdropFilter: 'blur(12px)',
      borderBottom: isAdmin ? '1px solid rgba(245, 158, 11, 0.3)' : '1px solid var(--border-subtle)',
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      padding: '0 24px',
      transition: 'all 0.25s ease'
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
          onClick={() => {
            if (isAdmin) {
              setActiveTab('admin');
            } else {
              setActiveTab('report');
            }
          }}
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        >
          <div style={{
            background: isAdmin 
              ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' 
              : 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: isAdmin 
              ? '0 2px 10px rgba(245, 158, 11, 0.4)' 
              : '0 2px 10px rgba(59, 130, 246, 0.4)'
          }}>
            <Shield size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '19px', fontWeight: 800, letterSpacing: '-0.02em', color: '#ffffff', fontFamily: 'var(--font-heading)' }}>
                CivicWatch
              </span>
              <span style={{
                background: isAdmin ? 'rgba(245, 158, 11, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                color: isAdmin ? '#fbbf24' : '#60a5fa',
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '4px',
                border: isAdmin ? '1px solid rgba(245, 158, 11, 0.35)' : '1px solid rgba(59, 130, 246, 0.3)'
              }}>
                {isAdmin ? 'OPERATIONS PORTAL' : 'CITIZEN PORTAL'}
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              {isAdmin ? 'Municipal Defect Triage & Verification Desk' : 'Public Road Surface Quality & AI Defect Reporting'}
            </div>
          </div>
        </div>

        {/* Dynamic Navigation according to Role */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {!isAdmin ? (
            /* CITIZEN NAV */
            <>
              <button
                onClick={() => setActiveTab('report')}
                className={`btn ${activeTab === 'report' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '8px 16px', fontSize: '13px' }}
              >
                <Shield size={15} />
                Report Defect
              </button>

              <button
                onClick={() => setActiveTab('map')}
                className={`btn ${activeTab === 'map' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '8px 16px', fontSize: '13px' }}
              >
                <MapPin size={15} />
                Public Defect Map
              </button>
            </>
          ) : (
            /* ADMIN NAV */
            <>
              <button
                onClick={() => setActiveTab('admin')}
                className={`btn ${activeTab === 'admin' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '8px 16px', fontSize: '13px' }}
              >
                <BarChart3 size={15} />
                Defect Triage & Tickets
              </button>

              <button
                onClick={() => setActiveTab('map')}
                className={`btn ${activeTab === 'map' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '8px 16px', fontSize: '13px' }}
              >
                <MapPin size={15} />
                City Incident Map
              </button>

              <button
                onClick={() => setActiveTab('telemetry')}
                className={`btn ${activeTab === 'telemetry' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '8px 16px', fontSize: '13px' }}
              >
                <Activity size={15} />
                CV Model Telemetry
              </button>
            </>
          )}
        </nav>

        {/* Portal Switcher & Auth State */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {!isAdmin ? (
            /* Citizen looking at the switch to Admin */
            <button
              onClick={() => {
                setViewMode('admin');
                setActiveTab('admin');
              }}
              className="btn btn-secondary"
              style={{
                fontSize: '12px',
                padding: '7px 14px',
                border: '1px solid rgba(245, 158, 11, 0.4)',
                color: '#fbbf24',
                background: 'rgba(245, 158, 11, 0.08)'
              }}
              title="Access Municipal Staff Dashboard"
            >
              <Lock size={13} />
              Municipal Staff Login
              <ArrowRight size={13} />
            </button>
          ) : (
            /* Admin view controls */
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <button
                onClick={() => {
                  setViewMode('citizen');
                  setActiveTab('report');
                }}
                className="btn btn-secondary"
                style={{
                  fontSize: '12px',
                  padding: '7px 12px',
                  background: 'rgba(59, 130, 246, 0.08)',
                  borderColor: 'rgba(59, 130, 246, 0.3)',
                  color: '#93c5fd'
                }}
              >
                <Eye size={13} />
                Switch to Citizen View
              </button>

              {adminUser ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {adminUser.user_name || adminUser.user_email}
                    </div>
                    <div style={{ fontSize: '10px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
                      <span className="pulse-dot" style={{ width: '6px', height: '6px' }}></span>
                      Admin Active
                    </div>
                  </div>
                  <button
                    onClick={onLogout}
                    className="btn btn-secondary"
                    style={{ padding: '6px 10px', borderRadius: '8px' }}
                    title="Log Out of Admin Operations"
                  >
                    <LogOut size={15} />
                  </button>
                </div>
              ) : (
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  (Not Authenticated)
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
