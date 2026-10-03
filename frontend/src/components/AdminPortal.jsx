import React, { useState, useEffect } from 'react';
import { 
  Lock, CheckCircle2, AlertCircle, Clock, CheckCheck, 
  XCircle, Search, Edit3, Eye, Zap, Save, RefreshCw, X 
} from 'lucide-react';

export default function AdminPortal({ adminToken, onLoginSuccess }) {
  // Login Form States
  const [loginEmail, setLoginEmail] = useState('harshithpataneni@gmail.com');
  const [loginPassword, setLoginPassword] = useState('admin123');
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState(null);

  // Dashboard Data States
  const [stats, setStats] = useState(null);
  const [reports, setReports] = useState([]);
  const [loadingData, setLoadingData] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Inspection Modal States
  const [selectedReport, setSelectedReport] = useState(null);
  const [modalStatus, setModalStatus] = useState('');
  const [modalNotes, setModalNotes] = useState('');
  const [activeModalView, setActiveModalView] = useState('original');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateMsg, setUpdateMsg] = useState(null);

  // Fetch Dashboard Stats & Reports
  const fetchDashboardData = async () => {
    if (!adminToken) return;
    setLoadingData(true);
    try {
      const [statsRes, reportsRes] = await Promise.all([
        fetch('/api/v1/admin/stats', {
          headers: { Authorization: `Bearer ${adminToken}` }
        }),
        fetch('/api/v1/reports?limit=200')
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
      if (reportsRes.ok) {
        const reportsData = await reportsRes.json();
        setReports(reportsData);
      }
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    if (adminToken) {
      fetchDashboardData();
    }
  }, [adminToken]);

  // Handle Login
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginLoading(true);
    setLoginError(null);

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password: loginPassword })
      });

      const data = await response.json();
      if (response.ok) {
        onLoginSuccess(data.access_token, data);
      } else {
        setLoginError(data.detail || 'Authentication failed. Please verify credentials.');
      }
    } catch (err) {
      setLoginError('Server connection error: ' + err.message);
    } finally {
      setLoginLoading(false);
    }
  };

  // Open Inspection Modal
  const openModal = async (reportItem) => {
    try {
      const res = await fetch(`/api/v1/reports/${reportItem.id}`);
      if (res.ok) {
        const fullReport = await res.json();
        setSelectedReport(fullReport);
        setModalStatus(fullReport.status);
        setModalNotes(fullReport.admin_notes || '');
        setUpdateMsg(null);
        setActiveModalView('original');
      }
    } catch (err) {
      console.error('Failed to load full report details:', err);
    }
  };

  // Save Status & Notes
  const handleSaveStatus = async () => {
    if (!selectedReport) return;
    setIsUpdating(true);
    setUpdateMsg(null);

    try {
      const response = await fetch(`/api/v1/reports/${selectedReport.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${adminToken}`
        },
        body: JSON.stringify({
          status: modalStatus,
          admin_notes: modalNotes
        })
      });

      if (response.ok) {
        const updated = await response.json();
        setSelectedReport(updated);
        setUpdateMsg({ type: 'success', text: 'Status and administrative notes updated successfully.' });
        fetchDashboardData(); // Refresh list
      } else {
        const err = await response.json();
        setUpdateMsg({ type: 'error', text: err.detail || 'Failed to update report status.' });
      }
    } catch (err) {
      setUpdateMsg({ type: 'error', text: 'Network error: ' + err.message });
    } finally {
      setIsUpdating(false);
    }
  };

  // Render Login Card if not authenticated
  if (!adminToken) {
    return (
      <div style={{ maxWidth: '440px', margin: '60px auto', padding: '0 16px' }}>
        <div className="glass-panel" style={{ padding: '36px 32px' }}>
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: 'rgba(59, 130, 246, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 12px'
            }}>
              <Lock size={24} color="#3b82f6" />
            </div>
            <h2 style={{ fontSize: '22px', color: '#ffffff' }}>Municipal Admin Login</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Authorized operations personnel portal
            </p>
          </div>

          {loginError && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#fca5a5',
              padding: '10px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              marginBottom: '16px'
            }}>
              {loginError}
            </div>
          )}

          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                Admin Email
              </label>
              <input
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  color: '#ffffff',
                  fontSize: '14px'
                }}
              />
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                Password
              </label>
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  color: '#ffffff',
                  fontSize: '14px'
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loginLoading}
              className="btn btn-primary"
              style={{ width: '100%', padding: '12px' }}
            >
              {loginLoading ? 'Authenticating...' : 'Sign In to Operations Console'}
            </button>
          </form>

          <div style={{
            marginTop: '20px',
            padding: '10px',
            borderRadius: '6px',
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            fontSize: '11px',
            color: 'var(--text-muted)'
          }}>
            Default Credentials: <code>admin@civicworks.org</code> / <code>admin_secure_change_me_123</code>
          </div>
        </div>
      </div>
    );
  }

  // Filtered reports
  const filteredReports = reports.filter((r) => {
    if (statusFilter !== 'ALL' && r.status !== statusFilter) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const matchId = r.public_id?.toLowerCase().includes(q);
      const matchAddr = r.address_text?.toLowerCase().includes(q);
      return matchId || matchAddr;
    }
    return true;
  });

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '28px 16px' }}>
      {/* Top Banner */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '26px', color: '#ffffff' }}>Operations Management Console</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Review, verify, and track municipal road repairs dispatched by the CV inference engine.
          </p>
        </div>
        <button onClick={fetchDashboardData} className="btn btn-secondary" style={{ fontSize: '13px' }}>
          <RefreshCw size={14} className={loadingData ? 'spinner' : ''} />
          Refresh Feed
        </button>
      </div>

      {/* Stats Counter Cards */}
      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          marginBottom: '28px'
        }}>
          <div className="glass-panel" style={{ padding: '18px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Total Ingested</div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#ffffff', marginTop: '4px' }}>
              {stats.total_reports}
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '18px' }}>
            <div style={{ fontSize: '11px', color: '#f59e0b', fontWeight: 600, textTransform: 'uppercase' }}>Pending Review</div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#fbbf24', marginTop: '4px' }}>
              {stats.status_breakdown.pending}
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '18px' }}>
            <div style={{ fontSize: '11px', color: '#06b6d4', fontWeight: 600, textTransform: 'uppercase' }}>Under Review</div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#22d3ee', marginTop: '4px' }}>
              {stats.status_breakdown.under_review}
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '18px' }}>
            <div style={{ fontSize: '11px', color: '#10b981', fontWeight: 600, textTransform: 'uppercase' }}>Resolved / Repaired</div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#34d399', marginTop: '4px' }}>
              {stats.status_breakdown.resolved}
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '18px' }}>
            <div style={{ fontSize: '11px', color: '#3b82f6', fontWeight: 600, textTransform: 'uppercase' }}>Avg AI Confidence</div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#60a5fa', marginTop: '4px' }}>
              {(stats.average_confidence * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="glass-panel" style={{
        padding: '16px 20px',
        marginBottom: '16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '260px', flex: 1 }}>
          <Search size={16} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search by Report ID (e.g. PH-2026-...) or location..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              borderRadius: '6px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              color: '#ffffff',
              fontSize: '13px'
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Status:</span>
          {['ALL', 'PENDING', 'UNDER_REVIEW', 'VERIFIED', 'RESOLVED', 'REJECTED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              style={{
                padding: '5px 10px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: 600,
                border: statusFilter === st ? '1px solid #3b82f6' : '1px solid var(--border-subtle)',
                background: statusFilter === st ? 'rgba(59, 130, 246, 0.2)' : 'var(--bg-surface)',
                color: statusFilter === st ? '#60a5fa' : 'var(--text-secondary)',
                cursor: 'pointer'
              }}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Reports Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-subtle)' }}>
              <th style={{ padding: '12px 16px', color: 'var(--text-muted)', fontWeight: 600 }}>PHOTO</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-muted)', fontWeight: 600 }}>REPORT ID</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-muted)', fontWeight: 600 }}>LOCATION</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-muted)', fontWeight: 600 }}>PRIORITY</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-muted)', fontWeight: 600 }}>CONFIDENCE</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-muted)', fontWeight: 600 }}>SEVERITY</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-muted)', fontWeight: 600 }}>STATUS</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-muted)', fontWeight: 600 }}>TIMESTAMP</th>
              <th style={{ padding: '12px 16px', color: 'var(--text-muted)', fontWeight: 600 }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {filteredReports.length === 0 ? (
              <tr>
                <td colSpan="9" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No reports matching filter criteria.
                </td>
              </tr>
            ) : (
              filteredReports.map((report) => (
                <tr 
                  key={report.id}
                  style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'background 0.15s ease' }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={{ padding: '10px 16px' }}>
                    <img
                      src={report.thumbnail_url || report.image_url}
                      alt="Thumbnail"
                      style={{ width: '48px', height: '36px', objectFit: 'cover', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}
                    />
                  </td>
                  <td style={{ padding: '10px 16px', fontWeight: 700, color: '#ffffff' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span>{report.public_id}</span>
                      {report.confirmations_count > 1 && (
                        <span className="badge badge-high" style={{ fontSize: '10px', padding: '2px 5px' }} title={`${report.confirmations_count} citizens reported this defect`}>
                          {report.confirmations_count}x
                        </span>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: '10px 16px', color: 'var(--text-secondary)', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {report.address_text || `${report.latitude.toFixed(4)}, ${report.longitude.toFixed(4)}`}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <span className={`badge badge-${report.user_priority?.toLowerCase()}`}>
                      {report.user_priority}
                    </span>
                  </td>
                  <td style={{ padding: '10px 16px', fontWeight: 600, color: '#60a5fa' }}>
                    {(report.model_confidence * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <span className={`badge badge-${report.estimated_severity?.toLowerCase()}`}>
                      {report.estimated_severity}
                    </span>
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <span className={`badge badge-${report.status?.toLowerCase()}`}>
                      {report.status}
                    </span>
                  </td>
                  <td style={{ padding: '10px 16px', color: 'var(--text-muted)', fontSize: '12px' }}>
                    {new Date(report.created_at).toLocaleDateString()} {new Date(report.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <button
                      onClick={() => openModal(report)}
                      className="btn btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '12px' }}
                    >
                      <Edit3 size={13} />
                      Review
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* DETAIL & STATUS MANAGEMENT MODAL */}
      {selectedReport && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          background: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(8px)',
          zIndex: 2000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div className="glass-panel" style={{
            maxWidth: '900px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '28px',
            position: 'relative'
          }}>
            <button
              onClick={() => setSelectedReport(null)}
              style={{
                position: 'absolute',
                top: '20px',
                right: '20px',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer'
              }}
            >
              <X size={20} />
            </button>

            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '22px', color: '#ffffff' }}>Defect Review: {selectedReport.public_id}</h2>
              <span className={`badge badge-${selectedReport.status.toLowerCase()}`}>{selectedReport.status}</span>
            </div>

            {updateMsg && (
              <div style={{
                background: updateMsg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                color: updateMsg.type === 'success' ? '#34d399' : '#fca5a5',
                padding: '10px 14px',
                borderRadius: '6px',
                fontSize: '13px',
                marginBottom: '16px'
              }}>
                {updateMsg.text}
              </div>
            )}

            {/* Two Column Layout */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px', marginBottom: '24px' }}>
              {/* Left Column: Visuals */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>INSPECTION ARTIFACTS</span>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button
                      type="button"
                      onClick={() => setActiveModalView('original')}
                      className={`btn ${activeModalView === 'original' ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ padding: '4px 10px', fontSize: '11px' }}
                    >
                      <Eye size={12} /> Original
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveModalView('heatmap')}
                      className={`btn ${activeModalView === 'heatmap' ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ padding: '4px 10px', fontSize: '11px' }}
                    >
                      <Zap size={12} /> Grad-CAM Heatmap
                    </button>
                  </div>
                </div>

                <div style={{
                  height: '320px',
                  borderRadius: 'var(--radius-md)',
                  overflow: 'hidden',
                  background: '#030712',
                  border: '1px solid var(--border-strong)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <img
                    src={activeModalView === 'original' ? selectedReport.image_url : (selectedReport.heatmap_url || selectedReport.image_url)}
                    alt="Defect visual"
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  />
                </div>
              </div>

              {/* Right Column: Model Telemetry & Status Form */}
              <div>
                {/* Telemetry info */}
                <div style={{ background: 'var(--bg-surface)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', marginBottom: '16px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#60a5fa', marginBottom: '10px' }}>
                    PYTORCH CV INFERENCE TELEMETRY
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '12px' }}>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Confidence:</span>
                      <div style={{ fontWeight: 700, color: '#ffffff' }}>{(selectedReport.model_confidence * 100).toFixed(1)}%</div>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Visual Severity:</span>
                      <div><span className={`badge badge-${selectedReport.estimated_severity.toLowerCase()}`}>{selectedReport.estimated_severity}</span></div>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Citizen Priority:</span>
                      <div><span className={`badge badge-${selectedReport.user_priority.toLowerCase()}`}>{selectedReport.user_priority}</span></div>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Model Version:</span>
                      <div style={{ fontWeight: 600, color: '#ffffff' }}>{selectedReport.model_version}</div>
                    </div>
                  </div>
                </div>

                {/* Location Box */}
                <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', marginBottom: '16px', fontSize: '12px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Location:</span>
                  <div style={{ fontWeight: 600, color: '#ffffff', marginTop: '2px' }}>{selectedReport.address_text || 'GPS Coordinates Recorded'}</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '2px' }}>
                    {selectedReport.latitude.toFixed(6)}, {selectedReport.longitude.toFixed(6)}
                  </div>
                </div>

                {/* Status Modification */}
                <div style={{ marginBottom: '14px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#ffffff', marginBottom: '4px' }}>
                    Update Operational Status
                  </label>
                  <select
                    value={modalStatus}
                    onChange={(e) => setModalStatus(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      color: '#ffffff',
                      fontSize: '13px'
                    }}
                  >
                    <option value="PENDING">PENDING (Awaiting Review)</option>
                    <option value="UNDER_REVIEW">UNDER REVIEW (Crew Dispatched)</option>
                    <option value="VERIFIED">VERIFIED (Work Order Approved)</option>
                    <option value="RESOLVED">RESOLVED (Pothole Repaired)</option>
                    <option value="REJECTED">REJECTED (Not a Municipal Defect)</option>
                  </select>
                </div>

                {/* Admin Notes */}
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#ffffff', marginBottom: '4px' }}>
                    Administrative & Work Order Notes
                  </label>
                  <textarea
                    rows="3"
                    value={modalNotes}
                    onChange={(e) => setModalNotes(e.target.value)}
                    placeholder="Enter crew assignment, repair dates, or closure remarks..."
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      color: '#ffffff',
                      fontSize: '13px',
                      resize: 'none'
                    }}
                  />
                </div>

                <button
                  type="button"
                  disabled={isUpdating}
                  onClick={handleSaveStatus}
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                >
                  <Save size={15} />
                  {isUpdating ? 'Saving Changes...' : 'Save Status & Notes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
