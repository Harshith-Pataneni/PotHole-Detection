import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { Filter, Layers, RefreshCw } from 'lucide-react';

const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#3b82f6'
};

export default function DefectMap({ onSelectReport }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);

  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');

  // Load Reports
  const fetchReports = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/reports?limit=200');
      if (response.ok) {
        const data = await response.json();
        setReports(data);
      }
    } catch (err) {
      console.error('Failed to load map reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Default center (San Francisco / California or user fallback)
    const map = L.map(mapContainerRef.current, {
      center: [37.7749, -122.4194],
      zoom: 12,
      zoomControl: true
    });

    // Standard OpenStreetMap tile layer (Reliable, free, no API key needed)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(map);

    markersLayerRef.current = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;

    // Force map to re-measure container size in case rendered inside tabs
    setTimeout(() => {
      map.invalidateSize();
    }, 250);

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Markers on Data / Filter change
  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current) return;

    markersLayerRef.current.clearLayers();

    const filtered = reports.filter((r) => {
      if (statusFilter !== 'ALL' && r.status !== statusFilter) return false;
      if (severityFilter !== 'ALL' && r.estimated_severity !== severityFilter) return false;
      return true;
    });

    const bounds = [];

    filtered.forEach((report) => {
      const lat = report.latitude;
      const lon = report.longitude;
      if (typeof lat !== 'number' || typeof lon !== 'number') return;

      bounds.push([lat, lon]);
      const color = SEVERITY_COLORS[report.estimated_severity] || '#3b82f6';

      // Custom circle marker with pulsing glow
      const marker = L.circleMarker([lat, lon], {
        radius: 8,
        fillColor: color,
        color: '#ffffff',
        weight: 2,
        opacity: 0.9,
        fillOpacity: 0.85
      });

      const popupHtml = `
        <div style="font-family: -apple-system, sans-serif; min-width: 200px; padding: 2px;">
          <div style="font-weight: 700; font-size: 13px; color: #0f172a; margin-bottom: 2px;">
            ${report.public_id}
          </div>
          <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">
            ${report.address_text || `${lat.toFixed(4)}, ${lon.toFixed(4)}`}
          </div>
          <div style="display: flex; gap: 4px; margin-bottom: 8px;">
            <span style="font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; background: #e2e8f0; color: #334155;">
              ${report.status}
            </span>
            <span style="font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; background: ${color}22; color: ${color};">
              ${report.estimated_severity}
            </span>
          </div>
          ${report.thumbnail_url ? `<img src="${report.thumbnail_url}" style="width: 100%; height: 90px; object-fit: cover; border-radius: 4px; margin-bottom: 8px;" />` : ''}
          <button id="view-report-${report.id}" style="width: 100%; background: #2563eb; color: #fff; border: none; padding: 6px; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer;">
            Inspect Defect &rarr;
          </button>
        </div>
      `;

      marker.bindPopup(popupHtml);
      marker.on('popupopen', () => {
        const btn = document.getElementById(`view-report-${report.id}`);
        if (btn) {
          btn.onclick = () => onSelectReport && onSelectReport(report);
        }
      });

      markersLayerRef.current.addLayer(marker);
    });

    if (bounds.length > 0 && mapInstanceRef.current) {
      mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
  }, [reports, statusFilter, severityFilter]);

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px 16px' }}>
      {/* Top Filter Bar */}
      <div className="glass-panel" style={{
        padding: '16px 20px',
        marginBottom: '16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={18} color="#3b82f6" />
          <span style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff' }}>
            Municipal Road Surface Defect Map
          </span>
          <span style={{
            fontSize: '11px',
            color: 'var(--text-muted)',
            background: 'var(--bg-surface)',
            padding: '2px 8px',
            borderRadius: '999px'
          }}>
            {reports.length} Reports Logged
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              color: '#ffffff',
              fontSize: '12px'
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="UNDER_REVIEW">Under Review</option>
            <option value="VERIFIED">Verified</option>
            <option value="RESOLVED">Resolved</option>
            <option value="REJECTED">Rejected</option>
          </select>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              color: '#ffffff',
              fontSize: '12px'
            }}
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <button
            onClick={fetchReports}
            className="btn btn-secondary"
            style={{ padding: '6px 10px', fontSize: '12px' }}
            title="Refresh Map Data"
          >
            <RefreshCw size={13} className={loading ? 'spinner' : ''} />
          </button>
        </div>
      </div>

      {/* Map Container */}
      <div className="glass-panel" style={{
        height: '620px',
        width: '100%',
        overflow: 'hidden',
        position: 'relative',
        borderRadius: 'var(--radius-lg)'
      }}>
        <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }}></div>

        {/* Legend Overlay */}
        <div style={{
          position: 'absolute',
          bottom: '20px',
          right: '20px',
          background: 'rgba(10, 15, 29, 0.9)',
          backdropFilter: 'blur(10px)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          padding: '10px 14px',
          zIndex: 1000,
          fontSize: '11px',
          color: '#ffffff'
        }}>
          <div style={{ fontWeight: 700, marginBottom: '6px', color: 'var(--text-secondary)' }}>SEVERITY TIERS</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }}></span>
              Critical Severity
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f97316' }}></span>
              High Severity
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#eab308' }}></span>
              Medium Severity
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#3b82f6' }}></span>
              Low Severity
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
