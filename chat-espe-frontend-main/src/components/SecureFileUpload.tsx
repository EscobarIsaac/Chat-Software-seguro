import React, { useState, useRef } from 'react';

interface SecurityReport {
  threat_level: string;
  confidence: number;
  warnings?: string[];
}

interface FileValidationResult {
  isValid: boolean;
  errors: string[];
  fileInfo?: {
    name: string;
    size: number;
    type: string;
    data?: string;
    hash?: string;
    category?: string;
    sanitized?: boolean;
  };
  securityReport?: SecurityReport;
  warnings?: string[];
}

interface SecureFileUploadProps {
  onFileValidated: (file: File, validationResult: FileValidationResult) => void;
  maxSize?: number;
  allowedTypes?: string[];
  disabled?: boolean;
}

// Función para obtener la URL base de la API
const getApiBase = () => {
  return import.meta.env.MODE === 'production'
    ? 'https://chat-espe-backend-production.up.railway.app'
    : `http://${window.location.hostname}:5000`;
};

const SecureFileUpload: React.FC<SecureFileUploadProps> = ({
  onFileValidated,
  maxSize = 50 * 1024 * 1024, // 50MB
  allowedTypes = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4',
    'video/mp4', 'video/avi', 'video/mkv', 'video/webm',
    'application/pdf', 'text/plain'
  ],
  disabled = false
}) => {
  const [uploading, setUploading] = useState(false);
  const [validationResult, setValidationResult] = useState<FileValidationResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFileClientSide = (file: File): FileValidationResult => {
    const errors: string[] = [];

    // Validar tamaño
    if (file.size > maxSize) {
      errors.push(`El archivo excede el tamaño máximo de ${Math.round(maxSize / (1024 * 1024))}MB`);
    }

    // Validar tipo MIME
    if (!allowedTypes.includes(file.type)) {
      errors.push(`Tipo de archivo no permitido: ${file.type}`);
    }

    // Validar extensión
    const allowedExtensions = [
      '.jpg', '.jpeg', '.png', '.gif', '.webp',
      '.mp3', '.wav', '.ogg', '.m4a',
      '.mp4', '.avi', '.mkv', '.webm',
      '.pdf', '.txt'
    ];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    if (!allowedExtensions.includes(fileExtension)) {
      errors.push(`Extensión de archivo no permitida: ${fileExtension}`);
    }

    // Validar nombre del archivo por caracteres sospechosos
    if (/[<>:"/\\|?*]/.test(file.name) || file.name.includes('..')) {
      errors.push('Nombre de archivo contiene caracteres no permitidos');
    }

    // Validar que no sea demasiado pequeño (podría ser sospechoso)
    if (file.size < 100) {
      errors.push('El archivo es demasiado pequeño para ser válido');
    }

    return {
      isValid: errors.length === 0,
      errors,
      fileInfo: {
        name: file.name,
        size: file.size,
        type: file.type
      }
    };
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setValidationResult(null);

    try {
      // Validación del lado del cliente
      const clientValidation = validateFileClientSide(file);
            
      if (!clientValidation.isValid) {
        setValidationResult(clientValidation);
        setUploading(false);
        return;
      }

      // Enviar al servidor para validación completa
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${getApiBase()}/api/upload-file`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        const successResult: FileValidationResult = {
          isValid: true,
          errors: [],
          fileInfo: {
            name: result.fileInfo?.name || result.filename,
            size: result.fileInfo?.size || result.size,
            type: result.fileInfo?.type || result.mime_type,
            data: result.fileInfo?.data || result.file_data,
            hash: result.fileInfo?.hash || result.hash,
            category: result.fileInfo?.category,
            sanitized: result.fileInfo?.sanitized
          },
          securityReport: result.security_report,
          warnings: result.warnings
        };
        setValidationResult(successResult);
        onFileValidated(file, successResult);
      } else {
        const errorResult: FileValidationResult = {
          isValid: false,
          errors: result.details || [result.error || result.message],
          fileInfo: clientValidation.fileInfo
        };
        setValidationResult(errorResult);
      }
    } catch (error) {
      const errorResult: FileValidationResult = {
        isValid: false,
        errors: ['Error de conexión con el servidor'],
        fileInfo: {
          name: file.name,
          size: file.size,
          type: file.type
        }
      };
      setValidationResult(errorResult);
    } finally {
      setUploading(false);
    }
  };

  const resetUpload = () => {
    setValidationResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getThreatLevelIcon = (level: string): string => {
    switch (level) {
      case 'critical': return '🚫';
      case 'high': return '❌';
      case 'medium': return '⚠️';
      case 'low': return '🔍';
      case 'safe': return '✅';
      default: return '❓';
    }
  };

  const getThreatLevelText = (level: string): string => {
    switch (level) {
      case 'critical': return 'AMENAZA CRÍTICA';
      case 'high': return 'Alto Riesgo';
      case 'medium': return 'Riesgo Medio';
      case 'low': return 'Riesgo Bajo';
      case 'safe': return 'Seguro';
      default: return 'Desconocido';
    }
  };

  return (
    <div className="secure-file-upload">
      <div className="upload-area">
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          disabled={uploading || disabled}
          accept={allowedTypes.join(',')}
          style={{ display: 'none' }}
        />
                
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading || disabled}
          className="upload-button"
        >
          {uploading ? '🔍 Análisis de seguridad en progreso...' : '🛡️ Subir archivo (Análisis de seguridad)'}
        </button>
        
        <div className="security-info">
          <small>
            ⚠️ Sistema avanzado: Detección de steganografía, malware y anomalías
          </small>
        </div>
      </div>

      {validationResult && (
        <div className={`validation-result ${validationResult.isValid ? 'success' : 'error'}`}>
          {validationResult.isValid ? (
            <div className="success-message">
              <div className="success-header">
                ✅ Archivo validado y seguro
                {validationResult.fileInfo?.sanitized && <span className="sanitized-badge">✨ Sanitizado</span>}
              </div>
              
              <div className="file-info">
                <p><strong>Nombre:</strong> {validationResult.fileInfo?.name}</p>
                <p><strong>Tamaño:</strong> {formatFileSize(validationResult.fileInfo?.size || 0)}</p>
                <p><strong>Tipo:</strong> {validationResult.fileInfo?.type}</p>
                {validationResult.fileInfo?.category && (
                  <p><strong>Categoría:</strong> {validationResult.fileInfo.category}</p>
                )}
                {validationResult.fileInfo?.hash && (
                  <p><strong>Hash:</strong> <code>{validationResult.fileInfo.hash.substring(0, 16)}...</code></p>
                )}
              </div>
              
              {validationResult.securityReport && (
                <div className="security-report">
                  <div className="security-header">🛡️ Análisis de Seguridad</div>
                  <div className="security-status">
                    <span className={`threat-level ${validationResult.securityReport.threat_level}`}>
                      {getThreatLevelIcon(validationResult.securityReport.threat_level)} 
                      {getThreatLevelText(validationResult.securityReport.threat_level)}
                    </span>
                    {validationResult.securityReport.confidence > 0 && (
                      <span className="confidence">Confianza: {(validationResult.securityReport.confidence * 100).toFixed(0)}%</span>
                    )}
                  </div>
                </div>
              )}
              
              {validationResult.warnings && validationResult.warnings.length > 0 && (
                <div className="warnings">
                  <div className="warnings-header">⚠️ Advertencias:</div>
                  <ul>
                    {validationResult.warnings.slice(0, 3).map((warning, idx) => (
                      <li key={idx}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="error-message">
              <div className="error-header">❌ Archivo rechazado</div>
              <ul className="error-list">
                {validationResult.errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
              <button onClick={resetUpload} className="retry-button">
                Intentar con otro archivo
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SecureFileUpload;