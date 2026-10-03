import React, { useState, useRef } from 'react';
import { 
  UploadCloud, MapPin, CheckCircle, AlertTriangle, RefreshCw, 
  Eye, Zap, ShieldAlert, Sparkles, Navigation, Info 
} from 'lucide-react';

const PROCESSING_STEPS = [
  "Uploading road surface imagery securely...",
  "Running PyTorch ResNet-50 transfer learning classifier...",
  "Extracting Grad-CAM spatial activation heatmaps...",
  "Calculating rule-based visual severity...",
  "Registering official municipal record in database..."
];

export default function ReportForm({ onReportSubmitted }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [coords, setCoords] = useState({ lat: '', lon: '' });
  const [address, setAddress] = useState('');
  const [geoStatus, setGeoStatus] = useState('idle'); // 'idle' | 'locating' | 'success' | 'error'
  const [priority, setPriority] = useState('MEDIUM');
  
  // Processing & Result States
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [activeImageView, setActiveImageView] = useState('original'); // 'original' | 'heatmap'
  const [errorMsg, setErrorMsg] = useState(null);

  const fileInputRef = useRef(null);

  // File Handlers
  const handleFileChange = (selectedFile) => {
    if (!selectedFile) return;

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(selectedFile.type)) {
      setErrorMsg('Please upload a valid image file (JPEG, PNG, or WebP).');
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setErrorMsg('Image size exceeds 10MB limit. Please upload a compressed photo.');
      return;
    }

    setErrorMsg(null);
    setFile(selectedFile);
    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);

    // Auto-request location if not already acquired
    if (geoStatus === 'idle') {
      requestLocation();
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  // Browser Geolocation API
  const requestLocation = () => {
    if (!navigator.geolocation) {
      setGeoStatus('error');
      setErrorMsg('Geolocation is not supported by your browser. Please enter coordinates manually.');
      return;
    }

    setGeoStatus('locating');
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = parseFloat(pos.coords.latitude.toFixed(6));
        const lon = parseFloat(pos.coords.longitude.toFixed(6));
        setCoords({ lat, lon });
        setGeoStatus('success');

        // Reverse geocode via free Nominatim
        try {
          const resp = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=jsonv2&zoom=16`);
          if (resp.ok) {
            const data = await resp.json();
            const addr = data.address || {};
            const road = addr.road || addr.street || addr.suburb || 'Current Roadway';
            const city = addr.city || addr.town || addr.village || '';
            setAddress(`${road}${city ? ', ' + city : ''}`);
          }
        } catch {
          setAddress('Coordinates Acquired');
        }
      },
      (err) => {
        console.warn('Geolocation permission error:', err);
        setGeoStatus('error');
        // Provide gentle default fallback for demo if permission was denied
        if (!coords.lat) {
          setCoords({ lat: 37.7749, lon: -122.4194 });
          setAddress('San Francisco, CA (Default Fallback)');
        }
      },
      { timeout: 8000, enableHighAccuracy: true }
    );
  };

  // Submit Handler
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      setErrorMsg('Please select or capture a photo of the suspected defect.');
      return;
    }

    if (!coords.lat || !coords.lon) {
      setErrorMsg('Location coordinates are required to dispatch road inspection teams.');
      return;
    }

    setErrorMsg(null);
    setIsSubmitting(true);
    setCurrentStepIdx(0);

    // Step cycle animation
    const interval = setInterval(() => {
      setCurrentStepIdx((prev) => (prev < PROCESSING_STEPS.length - 1 ? prev + 1 : prev));
    }, 900);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('latitude', coords.lat);
    formData.append('longitude', coords.lon);
    formData.append('user_priority', priority);

    try {
      const response = await fetch('/api/v1/reports', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      clearInterval(interval);
      setIsSubmitting(false);

      if (response.ok) {
        setSubmissionResult(data);
        if (data.success && onReportSubmitted) {
          onReportSubmitted(data.report);
        }
      } else {
        setErrorMsg(data.detail || 'Server encountered an error while processing report.');
      }
    } catch (err) {
      clearInterval(interval);
      setIsSubmitting(false);
      setErrorMsg('Network error communicating with the civic backend: ' + err.message);
    }
  };

  const resetForm = () => {
    setFile(null);
    setPreviewUrl(null);
    setSubmissionResult(null);
    setErrorMsg(null);
    setActiveImageView('original');
  };

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', padding: '32px 16px' }}>
      {/* Title */}
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 14px',
          borderRadius: '9999px',
          background: 'rgba(59, 130, 246, 0.12)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          color: '#60a5fa',
          fontSize: '13px',
          fontWeight: 600,
          marginBottom: '12px'
        }}>
          <Sparkles size={15} />
          Municipal Road Maintenance & Defect Intelligence
        </div>
        <h1 style={{ fontSize: '34px', color: '#ffffff', marginBottom: '8px' }}>
          Report a Pothole or Road Defect
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '15px', maxWidth: '580px', margin: '0 auto' }}>
          Upload a clear photo of the asphalt surface. Our onboard PyTorch Computer Vision pipeline
          verifies defect authenticity and calculates estimated visual severity in real time.
        </p>
      </div>

      {errorMsg && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#fca5a5',
          padding: '14px 18px',
          borderRadius: 'var(--radius-md)',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          fontSize: '14px'
        }}>
          <AlertTriangle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* RESULT VIEW (If Submitted) */}
      {submissionResult ? (
        <div className="glass-panel" style={{ padding: '32px' }}>
          {submissionResult.verified ? (
            /* VERIFIED POTHOLE VIEW */
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '24px' }}>
                <div style={{
                  background: 'rgba(16, 185, 129, 0.15)',
                  width: '52px',
                  height: '52px',
                  borderRadius: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '1px solid rgba(16, 185, 129, 0.3)'
                }}>
                  <CheckCircle size={28} color="#10b981" />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <h2 style={{ fontSize: '22px', color: '#ffffff' }}>
                      {submissionResult.is_duplicate ? 'Existing Defect Confirmed & Upvoted' : 'Pothole Verified & Report Filed'}
                    </h2>
                    <span className="badge badge-verified">{submissionResult.report.public_id}</span>
                    {submissionResult.confirmations_count > 1 && (
                      <span className="badge badge-high" style={{ fontSize: '11px' }}>
                        {submissionResult.confirmations_count}x Confirmed
                      </span>
                    )}
                  </div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '4px' }}>
                    {submissionResult.is_duplicate
                      ? 'A ticket already exists for this exact road location. Your submission has verified and raised priority on this existing defect without creating redundant tickets!'
                      : 'Report has been registered in the municipal queue with automated administrative notification.'}
                  </p>
                </div>
              </div>

              {submissionResult.is_duplicate && (
                <div style={{
                  background: 'rgba(59, 130, 246, 0.1)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 16px',
                  marginBottom: '20px',
                  fontSize: '13px',
                  color: '#93c5fd',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}>
                  <Sparkles size={18} color="#60a5fa" />
                  <span>
                    <strong>Smart Redundancy Shield:</strong> {submissionResult.guidance}
                  </span>
                </div>
              )}

              {/* Telemetry Stats Banner */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '12px',
                marginBottom: '24px'
              }}>
                <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Model Confidence</div>
                  <div style={{ fontSize: '20px', fontWeight: 700, color: '#3b82f6', marginTop: '4px' }}>
                    {(submissionResult.confidence * 100).toFixed(1)}%
                  </div>
                </div>

                <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Estimated Severity</div>
                  <div style={{ marginTop: '4px' }}>
                    <span className={`badge badge-${submissionResult.estimated_severity.toLowerCase()}`}>
                      {submissionResult.estimated_severity}
                    </span>
                  </div>
                </div>

                <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Citizen Priority</div>
                  <div style={{ marginTop: '4px' }}>
                    <span className={`badge badge-${submissionResult.report.user_priority.toLowerCase()}`}>
                      {submissionResult.report.user_priority}
                    </span>
                  </div>
                </div>

                <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Status</div>
                  <div style={{ marginTop: '4px' }}>
                    <span className="badge badge-pending">PENDING REVIEW</span>
                  </div>
                </div>
              </div>

              {/* Image Switcher (Original vs Grad-CAM Heatmap) */}
              <div style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Visual Verification Artifacts
                  </div>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      type="button"
                      onClick={() => setActiveImageView('original')}
                      className={`btn ${activeImageView === 'original' ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ padding: '6px 12px', fontSize: '12px' }}
                    >
                      <Eye size={14} />
                      Original Photo
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveImageView('heatmap')}
                      className={`btn ${activeImageView === 'heatmap' ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ padding: '6px 12px', fontSize: '12px' }}
                    >
                      <Zap size={14} />
                      AI Grad-CAM Heatmap
                    </button>
                  </div>
                </div>

                <div style={{
                  position: 'relative',
                  width: '100%',
                  height: '380px',
                  borderRadius: 'var(--radius-md)',
                  overflow: 'hidden',
                  background: '#030712',
                  border: '1px solid var(--border-strong)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <img
                    src={activeImageView === 'original' ? submissionResult.report.image_url : (submissionResult.report.heatmap_url || submissionResult.report.image_url)}
                    alt="Road defect verification"
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  />
                  <div style={{
                    position: 'absolute',
                    bottom: '12px',
                    left: '12px',
                    background: 'rgba(0, 0, 0, 0.75)',
                    backdropFilter: 'blur(8px)',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    fontSize: '11px',
                    color: '#ffffff'
                  }}>
                    {activeImageView === 'original' 
                      ? 'Client Uploaded Image' 
                      : 'ResNet-50 Layer4 Spatial Feature Map Activation (Grad-CAM)'}
                  </div>
                </div>
              </div>

              {/* Location details */}
              <div style={{
                background: 'var(--bg-surface)',
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                marginBottom: '24px',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <MapPin size={18} color="#3b82f6" />
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: 600, color: '#ffffff' }}>
                      {submissionResult.report.address_text || 'GPS Coordinates Recorded'}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      Latitude: {submissionResult.report.latitude.toFixed(6)}, Longitude: {submissionResult.report.longitude.toFixed(6)}
                    </div>
                  </div>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Model v1 &bull; PyTorch ResNet-50
                </div>
              </div>

              <button onClick={resetForm} className="btn btn-secondary" style={{ width: '100%' }}>
                <RefreshCw size={16} />
                Submit Another Report
              </button>
            </div>
          ) : (
            /* UNVERIFIED / LOW CONFIDENCE REJECTION VIEW (Section 10) */
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 20px'
              }}>
                <ShieldAlert size={32} color="#ef4444" />
              </div>
              <h2 style={{ fontSize: '22px', color: '#ffffff', marginBottom: '10px' }}>
                Defect Not Confidently Verified
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '14px', maxWidth: '480px', margin: '0 auto 20px', lineHeight: 1.6 }}>
                Our Computer Vision model analyzed the image with <strong style={{ color: '#f87171' }}>{(submissionResult.confidence * 100).toFixed(1)}% confidence</strong>, which is below our municipal verification threshold of 75%.
              </p>
              <div style={{
                background: 'var(--bg-surface)',
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                maxWidth: '460px',
                margin: '0 auto 24px',
                textAlign: 'left',
                border: '1px solid var(--border-subtle)',
                fontSize: '13px',
                color: 'var(--text-secondary)'
              }}>
                <div style={{ fontWeight: 600, color: '#ffffff', marginBottom: '4px' }}>Photographic Guidelines:</div>
                <ul style={{ paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <li>Capture the pavement directly in daylight.</li>
                  <li>Ensure the pothole edges and road texture are in clear focus.</li>
                  <li>Avoid heavy glare, blurred motion, or dashboard obstructions.</li>
                </ul>
              </div>
              <button onClick={resetForm} className="btn btn-primary" style={{ minWidth: '220px' }}>
                <RefreshCw size={16} />
                Retry with a Clearer Photo
              </button>
            </div>
          )}
        </div>
      ) : (
        /* STANDARD SUBMISSION FORM */
        <form onSubmit={handleSubmit} className="glass-panel" style={{ padding: '32px' }}>
          {/* 1. Upload Zone */}
          <div style={{ marginBottom: '28px' }}>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>
              1. Road Surface Photo <span style={{ color: '#ef4444' }}>*</span>
            </label>

            {!previewUrl ? (
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: '2px dashed var(--border-strong)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '44px 20px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  background: 'rgba(31, 41, 55, 0.3)',
                  transition: 'all 0.2s ease'
                }}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(e) => handleFileChange(e.target.files[0])}
                  style={{ display: 'none' }}
                />
                <div style={{
                  width: '54px',
                  height: '54px',
                  borderRadius: '12px',
                  background: 'rgba(59, 130, 246, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 16px'
                }}>
                  <UploadCloud size={28} color="#3b82f6" />
                </div>
                <div style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff', marginBottom: '4px' }}>
                  Click to upload or drag & drop road image
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Supports JPEG, PNG, WebP up to 10MB
                </div>
              </div>
            ) : (
              <div style={{ position: 'relative', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-strong)' }}>
                <img
                  src={previewUrl}
                  alt="Upload preview"
                  style={{ width: '100%', height: '320px', objectFit: 'cover', display: 'block' }}
                />
                <button
                  type="button"
                  onClick={() => { setFile(null); setPreviewUrl(null); }}
                  className="btn btn-secondary"
                  style={{
                    position: 'absolute',
                    top: '12px',
                    right: '12px',
                    background: 'rgba(0, 0, 0, 0.75)',
                    backdropFilter: 'blur(8px)',
                    fontSize: '12px',
                    padding: '6px 12px'
                  }}
                >
                  Change Image
                </button>
              </div>
            )}
          </div>

          {/* 2. Geolocation Section */}
          <div style={{ marginBottom: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label style={{ fontSize: '14px', fontWeight: 600, color: '#ffffff' }}>
                2. Defect GPS Location <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <button
                type="button"
                onClick={requestLocation}
                className="btn btn-secondary"
                disabled={geoStatus === 'locating'}
                style={{ fontSize: '12px', padding: '6px 12px' }}
              >
                <Navigation size={13} />
                {geoStatus === 'locating' ? 'Acquiring GPS...' : 'Use Current GPS'}
              </button>
            </div>

            <div style={{
              background: 'var(--bg-surface)',
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <span className="pulse-dot" style={{ backgroundColor: geoStatus === 'success' ? '#10b981' : '#f59e0b' }}></span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff' }}>
                  {geoStatus === 'success' ? (address || 'GPS Position Locked') : 'Location Required for Field Dispatch'}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Latitude
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={coords.lat}
                    onChange={(e) => setCoords({ ...coords, lat: parseFloat(e.target.value) || '' })}
                    placeholder="e.g. 37.7749"
                    required
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      background: 'var(--bg-surface-elevated)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '6px',
                      color: '#ffffff',
                      fontSize: '13px'
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Longitude
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={coords.lon}
                    onChange={(e) => setCoords({ ...coords, lon: parseFloat(e.target.value) || '' })}
                    placeholder="e.g. -122.4194"
                    required
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      background: 'var(--bg-surface-elevated)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '6px',
                      color: '#ffffff',
                      fontSize: '13px'
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 3. Citizen Priority Selector */}
          <div style={{ marginBottom: '32px' }}>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>
              3. Citizen Perceived Priority
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
              {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPriority(p)}
                  style={{
                    padding: '10px 8px',
                    borderRadius: 'var(--radius-md)',
                    border: priority === p ? '2px solid #3b82f6' : '1px solid var(--border-subtle)',
                    background: priority === p ? 'rgba(59, 130, 246, 0.2)' : 'var(--bg-surface)',
                    color: priority === p ? '#ffffff' : 'var(--text-secondary)',
                    fontWeight: 600,
                    fontSize: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Submission Processing State */}
          {isSubmitting ? (
            <div style={{
              background: 'var(--bg-surface)',
              borderRadius: 'var(--radius-md)',
              padding: '20px',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              textAlign: 'center'
            }}>
              <div className="spinner" style={{ margin: '0 auto 12px' }}></div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#ffffff', marginBottom: '4px' }}>
                AI Model Verification In Progress
              </div>
              <div style={{ fontSize: '12px', color: '#60a5fa' }}>
                {PROCESSING_STEPS[currentStepIdx]}
              </div>
            </div>
          ) : (
            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '14px', fontSize: '15px' }}
            >
              <Zap size={18} />
              Submit Road Defect for AI Verification
            </button>
          )}
        </form>
      )}
    </div>
  );
}
