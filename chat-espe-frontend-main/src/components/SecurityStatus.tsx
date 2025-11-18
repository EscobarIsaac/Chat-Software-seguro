// SecurityStatus.tsx - Componente para mostrar estado de seguridad
import React from 'react';

interface SecurityStatusProps {
  threatLevel: string;
  confidence: number;
  warnings?: string[];
  sanitized?: boolean;
  onClose?: () => void;
}

const SecurityStatus: React.FC<SecurityStatusProps> = ({
  threatLevel,
  confidence,
  warnings = [],
  sanitized = false,
  onClose
}) => {
  const getThreatLevelColor = () => {
    switch (threatLevel) {
      case 'critical': return '#dc2626';
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#3b82f6';
      case 'safe': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getThreatLevelIcon = () => {
    switch (threatLevel) {
      case 'critical': return '🚫';
      case 'high': return '❌';
      case 'medium': return '⚠️';
      case 'low': return '🔍';
      case 'safe': return '✅';
      default: return '❓';
    }
  };

  const getThreatLevelText = () => {
    switch (threatLevel) {
      case 'critical': return 'AMENAZA CRÍTICA';
      case 'high': return 'Alto Riesgo';
      case 'medium': return 'Riesgo Medio';
      case 'low': return 'Riesgo Bajo';
      case 'safe': return 'Seguro';
      default: return 'Desconocido';
    }
  };

  return (
    <div className="security-status-container" style={{
      position: 'fixed',
      top: '80px',
      right: '20px',
      backgroundColor: '#1e1e1e',
      border: `2px solid ${getThreatLevelColor()}`,
      borderRadius: '12px',
      padding: '20px',
      maxWidth: '400px',
      boxShadow: '0 10px 40px rgba(0,0,0,0.5)',
      zIndex: 1000,
      animation: 'slideInRight 0.3s ease-out'
    }}>
      <div className="security-header" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '15px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '24px' }}>{getThreatLevelIcon()}</span>
          <div>
            <div style={{ 
              color: getThreatLevelColor(), 
              fontWeight: 'bold',
              fontSize: '16px'
            }}>
              {getThreatLevelText()}
            </div>
            {confidence > 0 && (
              <div style={{ fontSize: '12px', color: '#999', marginTop: '2px' }}>
                Confianza: {(confidence * 100).toFixed(0)}%
              </div>
            )}
          </div>
        </div>
        {onClose && (
          <button 
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#999',
              cursor: 'pointer',
              fontSize: '20px',
              padding: '0',
              width: '24px',
              height: '24px'
            }}
          >
            ×
          </button>
        )}
      </div>

      {sanitized && (
        <div style={{
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid #10b981',
          borderRadius: '8px',
          padding: '10px',
          marginBottom: '10px',
          fontSize: '13px',
          color: '#10b981'
        }}>
          ✨ Archivo sanitizado automáticamente
        </div>
      )}

      {warnings.length > 0 && (
        <div className="security-warnings" style={{
          marginTop: '10px'
        }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: 'bold', 
            color: '#f59e0b',
            marginBottom: '8px'
          }}>
            ⚠️ Advertencias detectadas:
          </div>
          <ul style={{
            margin: 0,
            paddingLeft: '20px',
            fontSize: '12px',
            color: '#ccc'
          }}>
            {warnings.map((warning, idx) => (
              <li key={idx} style={{ marginBottom: '4px' }}>
                {warning}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="confidence-bar" style={{
        marginTop: '15px',
        height: '4px',
        backgroundColor: '#333',
        borderRadius: '2px',
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${confidence * 100}%`,
          height: '100%',
          backgroundColor: getThreatLevelColor(),
          transition: 'width 0.3s ease'
        }}/>
      </div>

      {threatLevel === 'safe' && (
        <div style={{
          marginTop: '10px',
          fontSize: '11px',
          color: '#666',
          textAlign: 'center'
        }}>
          Análisis completado • Sin amenazas detectadas
        </div>
      )}
    </div>
  );
};

export default SecurityStatus;