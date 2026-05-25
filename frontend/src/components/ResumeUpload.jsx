import React, { useState, useRef } from 'react';

export default function ResumeUpload({ onSessionStarted }) {
  const [file, setFile] = useState(null);
  const [role, setRole] = useState('backend_engineer');
  const [loading, setLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState('');
  const [error, setError] = useState('');
  const [isDragActive, setIsDragActive] = useState(false);
  
  const fileInputRef = useRef(null);

  const roles = [
    { id: 'backend_engineer', name: 'Backend Engineer', icon: '⚙️', desc: 'Evaluates API Design, Databases, System Design, Concurrency, and Security.' },
    { id: 'ai_ml_engineer', name: 'AI/ML Engineer', icon: '🧠', desc: 'Evaluates Concept Learning, Supervised Learning, Deep Learning, RAG, and NLP.' },
    { id: 'data_scientist', name: 'Data Scientist', icon: '📊', desc: 'Evaluates EDA, Statistics, Data Preprocessing, Ensembles, and Evaluation Metrics.' }
  ];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    setError('');
    const ext = selectedFile.name.split('.').pop().toLowerCase();
    if (ext !== 'pdf' && ext !== 'txt') {
      setError('Please upload a PDF or TXT file only.');
      setFile(null);
      return;
    }
    // Limit to 10MB
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File size exceeds the 10MB limit.');
      setFile(null);
      return;
    }
    setFile(selectedFile);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select or upload a resume.');
      return;
    }

    setLoading(true);
    setError('');
    
    // Smooth transition phases for loader
    setLoadingPhase('Uploading your resume...');
    const phaseTimer1 = setTimeout(() => setLoadingPhase('Parsing resume & extracting skills...'), 1200);
    const phaseTimer2 = setTimeout(() => setLoadingPhase('Initializing AI Interviewer context...'), 2800);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('role', role);

    try {
      const response = await fetch('/api/sessions/start', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to initialize session');
      }

      const data = await response.json();
      clearTimeout(phaseTimer1);
      clearTimeout(phaseTimer2);
      onSessionStarted(data);
    } catch (err) {
      clearTimeout(phaseTimer1);
      clearTimeout(phaseTimer2);
      setError(err.message || 'An error occurred while uploading. Please check if your backend is running.');
      setLoading(false);
    }
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s ease', maxWidth: '680px', margin: '2rem auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <h1 className="heading-display" style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>TalentAI</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
          Real-time AI technical screener powered by RAG and adaptive context generation.
        </p>
      </div>

      <div className="glass-panel">
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '4rem 2rem', minHeight: '320px' }}>
            <div className="spinner" style={{ width: '48px', height: '48px', borderWidth: '4px', marginBottom: '1.5rem' }}></div>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', marginBottom: '0.5rem' }}>Setting up your interview</h3>
            <p style={{ color: 'var(--text-secondary)', animation: 'fadeIn 0.3s ease' }}>{loadingPhase}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" style={{ marginBottom: '1rem', display: 'block', fontSize: '1rem', fontWeight: 600 }}>
                1. Select Target Job Role
              </label>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
                {roles.map((r) => (
                  <div 
                    key={r.id}
                    onClick={() => setRole(r.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      padding: '1.2rem',
                      borderRadius: 'var(--radius-md)',
                      background: role === r.id ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255, 255, 255, 0.02)',
                      border: role === r.id ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)'
                    }}
                  >
                    <span style={{ fontSize: '1.8rem' }}>{r.icon}</span>
                    <div style={{ flexGrow: 1 }}>
                      <h4 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '1rem', color: role === r.id ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                        {r.name}
                      </h4>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>{r.desc}</p>
                    </div>
                    <div style={{
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      border: '2px solid',
                      borderColor: role === r.id ? 'var(--primary)' : 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      justifycontent: 'center',
                      background: role === r.id ? 'var(--primary)' : 'transparent',
                      boxShadow: role === r.id ? '0 0 10px rgba(99, 102, 241, 0.5)' : 'none'
                    }}>
                      {role === r.id && (
                        <svg width="10" height="8" viewBox="0 0 10 8" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M1.5 4L4 6.5L8.5 1.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" style={{ marginBottom: '1rem', display: 'block', fontSize: '1rem', fontWeight: 600 }}>
                2. Upload Your Resume
              </label>
              
              <div 
                className={`dropzone ${isDragActive ? 'active' : ''}`}
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current.click()}
              >
                <input 
                  type="file" 
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                  accept=".pdf,.txt"
                />
                <span className="dropzone-icon" style={{ fontSize: '2.5rem' }}>📄</span>
                {file ? (
                  <div>
                    <h4 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, color: 'var(--accent-emerald)' }}>
                      Selected: {file.name}
                    </h4>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                      Click to choose a different file. {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                ) : (
                  <div>
                    <h4 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, color: 'var(--text-primary)' }}>
                      Drag and drop your resume file here
                    </h4>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                      Supports PDF or TXT up to 10MB
                    </p>
                  </div>
                )}
              </div>
            </div>

            {error && (
              <div style={{
                background: 'rgba(244, 63, 94, 0.1)',
                border: '1px solid rgba(244, 63, 94, 0.2)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--accent-rose)',
                padding: '1rem',
                margin: '1.5rem 0',
                fontSize: '0.9rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                ⚠️ <strong>Error:</strong> {error}
              </div>
            )}

            <button 
              type="submit" 
              className="btn btn-primary" 
              style={{ width: '100%', padding: '1rem', fontSize: '1.05rem', marginTop: '1rem' }}
              disabled={!file}
            >
              Start Technical Screening Interview
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
