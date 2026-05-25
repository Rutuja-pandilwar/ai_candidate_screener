import React, { useState, useEffect } from 'react';
import ResumeUpload from './components/ResumeUpload';
import InterviewStage from './components/InterviewStage';
import ReportStage from './components/ReportStage';

export default function App() {
  const [stage, setStage] = useState('upload'); // upload, interview, report
  const [session, setSession] = useState(null);
  const [backendStatus, setBackendStatus] = useState({ online: false, gemini: false });

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await fetch('/api/health');
      if (response.ok) {
        const data = await response.json();
        setBackendStatus({ online: true, gemini: data.gemini_api_configured });
      } else {
        setBackendStatus({ online: false, gemini: false });
      }
    } catch (err) {
      setBackendStatus({ online: false, gemini: false });
    }
  };

  const handleSessionStarted = (sessionData) => {
    setSession(sessionData);
    setStage('interview');
  };

  const handleInterviewFinished = () => {
    setStage('report');
  };

  const handleRestart = () => {
    setSession(null);
    setStage('upload');
  };

  return (
    <div>
      {/* Top Navbar */}
      <header style={{
        background: 'rgba(11, 13, 25, 0.8)',
        borderBottom: '1px solid var(--border-color)',
        backdropFilter: 'blur(10px)',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }} onClick={handleRestart}>
            <span style={{ fontSize: '1.8rem' }}>🤖</span>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.2rem', letterSpacing: '-0.02em' }}>
              Talent<span style={{ color: 'var(--primary)' }}>AI</span>
            </span>
          </div>

          {/* Backend Status indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <span style={{ 
                width: '8px', 
                height: '8px', 
                borderRadius: '50%', 
                background: backendStatus.online ? 'var(--accent-emerald)' : 'var(--accent-rose)' 
              }}></span>
              Server: {backendStatus.online ? 'Online' : 'Offline'}
            </div>

            {backendStatus.online && (
              <div style={{ 
                fontSize: '0.75rem', 
                background: backendStatus.gemini ? 'rgba(16, 185, 129, 0.08)' : 'rgba(244, 63, 94, 0.08)',
                color: backendStatus.gemini ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                padding: '0.2rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
                border: backendStatus.gemini ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid rgba(244, 63, 94, 0.2)',
                fontWeight: 600
              }}>
                {backendStatus.gemini ? 'Gemini Active' : 'Gemini Config Missing (Using Mock Mode)'}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="container" style={{ minHeight: 'calc(100vh - 10rem)', display: 'flex', flexDirection: 'column' }}>
        {stage === 'upload' && (
          <ResumeUpload onSessionStarted={handleSessionStarted} />
        )}

        {stage === 'interview' && session && (
          <InterviewStage 
            session={session} 
            onInterviewFinished={handleInterviewFinished} 
          />
        )}

        {stage === 'report' && session && (
          <ReportStage 
            session={session} 
            onRestart={handleRestart} 
          />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        textAlign: 'center',
        padding: '2rem 1.5rem',
        borderTop: '1px solid var(--border-color)',
        marginTop: 'auto',
        fontSize: '0.85rem',
        color: 'var(--text-muted)'
      }}>
        <p>© 2026 TalentAI Candidate Screener System. All rights reserved.</p>
        <p style={{ marginTop: '0.25rem' }}>Designed for AI/ML & Backend System Evaluation.</p>
      </footer>
    </div>
  );
}
