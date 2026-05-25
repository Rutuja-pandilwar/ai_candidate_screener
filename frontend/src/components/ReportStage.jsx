import React, { useState, useEffect } from 'react';

export default function ReportStage({ session, onRestart }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedQuestion, setExpandedQuestion] = useState(null);

  useEffect(() => {
    fetchReport();
  }, []);

  const fetchReport = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`/api/sessions/${session.id}/report`);
      if (!response.ok) {
        throw new Error('Failed to retrieve the interview report.');
      }
      const data = await response.json();
      setReport(data);
    } catch (err) {
      setError(err.message || 'An error occurred loading your evaluation report.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreBadgeClass = (score) => {
    if (score >= 8.5) return 'badge-excellent';
    if (score >= 7.0) return 'badge-good';
    if (score >= 5.0) return 'badge-average';
    return 'badge-fail';
  };

  const getScoreColor = (score) => {
    if (score >= 8.5) return 'var(--accent-emerald)';
    if (score >= 7.0) return 'var(--accent-blue)';
    if (score >= 5.0) return 'var(--accent-amber)';
    return 'var(--accent-rose)';
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '6rem 2rem', minHeight: '400px' }}>
        <div className="spinner" style={{ width: '48px', height: '48px', borderWidth: '4px', marginBottom: '1.5rem' }}></div>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem' }}>Compiling Final Engineering Report...</h3>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Aggregating scores, grading logs, and RAG trace vectors...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel" style={{ maxWidth: '600px', margin: '3rem auto', textAlign: 'center', padding: '3rem' }}>
        <span style={{ fontSize: '3rem' }}>⚠️</span>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', margin: '1rem 0' }}>Report Fetch Error</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>{error}</p>
        <button onClick={fetchReport} className="btn btn-primary">Try Again</button>
      </div>
    );
  }

  const summary = report.summary_report || {};
  const overallScore = report.overall_score || 0.0;
  
  // Calculate SVG stroke attributes
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  // Score is out of 10
  const strokeDashoffset = circumference - (overallScore / 10) * circumference;

  return (
    <div style={{ animation: 'fadeIn 0.6s ease' }}>
      {/* Header section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '1.5rem', marginBottom: '2rem', flexWrap: 'wrap', gap: '1.5rem' }}>
        <div>
          <span style={{ 
            fontSize: '0.8rem', 
            fontWeight: 700, 
            textTransform: 'uppercase', 
            background: 'rgba(16, 185, 129, 0.1)', 
            color: 'var(--accent-emerald)', 
            padding: '0.3rem 0.8rem', 
            borderRadius: 'var(--radius-full)',
            border: '1px solid rgba(16, 185, 129, 0.2)'
          }}>
            Screening Completed
          </span>
          <h1 className="heading-display" style={{ fontSize: '2.2rem', marginTop: '0.5rem' }}>
            Technical Evaluation Report
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginTop: '0.2rem' }}>
            Candidate: <strong>{report.candidate_name}</strong> | Role: <strong>{report.selected_role === 'ai_ml_engineer' ? 'AI/ML Engineer' : report.selected_role === 'backend_engineer' ? 'Backend Engineer' : 'Data Scientist'}</strong>
          </p>
        </div>

        <button onClick={onRestart} className="btn btn-primary" style={{ padding: '0.7rem 1.4rem', fontSize: '0.9rem' }}>
          🔄 Start New Screening
        </button>
      </div>

      {/* Main Analysis grid */}
      <div className="report-grid">
        {/* Score widget Card */}
        <div className="glass-panel score-widget">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '1.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Overall Rating
          </h3>
          
          <div className="circle-chart-container">
            <svg className="circle-chart-svg" width="160" height="160">
              <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="var(--primary)" />
                  <stop offset="100%" stopColor="var(--secondary)" />
                </linearGradient>
              </defs>
              <circle className="circle-chart-bg" cx="80" cy="80" r={radius} />
              <circle 
                className="circle-chart-fill" 
                cx="80" 
                cy="80" 
                r={radius} 
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
              />
            </svg>
            <div className="circle-chart-text">
              <span className="score-num" style={{ color: getScoreColor(overallScore) }}>
                {overallScore.toFixed(1)}
              </span>
              <span className="score-max">out of 10</span>
            </div>
          </div>

          <div style={{ 
            fontSize: '0.9rem', 
            fontWeight: 700, 
            color: getScoreColor(overallScore),
            background: `rgba(${overallScore >= 7.5 ? '16, 185, 129' : overallScore >= 5 ? '245, 158, 11' : '244, 63, 94'}, 0.08)`,
            padding: '0.4rem 1rem',
            borderRadius: 'var(--radius-full)',
            border: `1px solid rgba(${overallScore >= 7.5 ? '16, 185, 129' : overallScore >= 5 ? '245, 158, 11' : '244, 63, 94'}, 0.2)`
          }}>
            {overallScore >= 8.5 ? 'Strong Fit' : overallScore >= 7.0 ? 'Recommended' : overallScore >= 5.0 ? 'Borderline' : 'Not Recommended'}
          </div>
        </div>

        {/* Textual Insights Card */}
        <div className="insights-container">
          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', marginBottom: '0.75rem', display: 'flex', alignitems: 'center', gap: '0.5rem' }}>
              📋 Executive Assessment Summary
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
              {summary.summary || 'The candidate has completed the full technical screening. Detailed metrics on conceptual knowledge, system understanding, and coding depth are provided below.'}
            </p>
          </div>

          <div className="card-insight">
            {/* Strengths */}
            <div className="insight-block strengths">
              <h4 className="insight-title" style={{ color: 'var(--accent-emerald)' }}>
                ✅ Evaluated Strengths
              </h4>
              <ul className="insight-list">
                {(summary.strengths || ['Demonstrated foundational concepts', 'Clear structure of technical thoughts']).map((strength, idx) => (
                  <li key={idx} className="insight-item">{strength}</li>
                ))}
              </ul>
            </div>

            {/* Areas for Improvement */}
            <div className="insight-block weaknesses">
              <h4 className="insight-title" style={{ color: 'var(--accent-rose)' }}>
                🔍 Focus Areas & Improvements
              </h4>
              <ul className="insight-list">
                {(summary.areas_for_improvement || ['Provide deeper details on production configurations', 'Expand practical implementation reasoning']).map((weakness, idx) => (
                  <li key={idx} className="insight-item">{weakness}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Transcript / Accordion Trace */}
      <div className="transcript-section">
        <h3 className="transcript-header">Q&A Audit Trail & RAG Attribution</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Expand each question to inspect the candidate's answers, the LLM grading rationale, and the exact textbook reference sources retrieved via RAG.
        </p>

        <div className="transcript-list">
          {report.questions && report.questions.map((q, idx) => {
            const isExpanded = expandedQuestion === q.id;
            let RAGSources = [];
            if (q.context_retrieved) {
              try {
                RAGSources = JSON.parse(q.context_retrieved);
              } catch (e) {
                console.error("Failed to parse retrieved context JSON", e);
              }
            }

            return (
              <div 
                key={q.id} 
                className="transcript-card"
                style={{ borderColor: isExpanded ? 'var(--primary)' : 'var(--border-color)' }}
              >
                <div 
                  className="transcript-card-summary" 
                  onClick={() => setExpandedQuestion(isExpanded ? null : q.id)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', flexGrow: 1 }}>
                    <span style={{ fontSize: '1.1rem', color: isExpanded ? 'var(--primary)' : 'var(--text-muted)' }}>
                      {isExpanded ? '▼' : '▶'}
                    </span>
                    <span className="transcript-question-title">
                      Q{idx + 1}: {q.question_text.length > 85 ? q.question_text.substring(0, 85) + '...' : q.question_text}
                    </span>
                  </div>
                  <span className={`transcript-badge-score ${getScoreBadgeClass(q.score)}`}>
                    Score: {q.score !== null ? q.score.toFixed(1) : 'N/A'}/10
                  </span>
                </div>

                {isExpanded && (
                  <div className="transcript-card-content">
                    {/* Detailed Question */}
                    <div>
                      <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem', letterSpacing: '0.05em' }}>
                        Full Question Asked
                      </h4>
                      <p style={{ fontSize: '0.95rem', color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                        {q.question_text}
                      </p>
                    </div>

                    {/* RAG trace */}
                    {RAGSources.length > 0 && (
                      <div className="trace-box">
                        <div className="trace-title">
                          🔍 RAG Grounding Search Trace
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.3rem' }}>
                          {RAGSources.map((source, sIdx) => (
                            <div key={sIdx} style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                              <span>📖 <strong>Document:</strong> {source.document} (Chunk ID: {source.chunk_id})</span>
                              <span style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>
                                Cosine Similarity: {(source.score * 100).toFixed(1)}% Match
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Candidate Answer */}
                    <div style={{ marginTop: '0.5rem' }}>
                      <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem', letterSpacing: '0.05em' }}>
                        Candidate Answer Response
                      </h4>
                      <pre style={{ 
                        background: '#070913', 
                        padding: '1.2rem', 
                        borderRadius: 'var(--radius-sm)', 
                        fontFamily: 'Courier New, monospace', 
                        fontSize: '0.9rem',
                        color: '#cbd5e1',
                        whiteSpace: 'pre-wrap',
                        overflowX: 'auto',
                        border: '1px solid var(--border-color)'
                      }}>
                        {q.candidate_answer || '[Candidate exited early before answering this question]'}
                      </pre>
                    </div>

                    {/* Expected Guidelines */}
                    <div style={{ marginTop: '0.5rem' }}>
                      <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.3rem', letterSpacing: '0.05em' }}>
                        Evaluation Rubric Guidelines
                      </h4>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                        {q.correct_answer_guideline}
                      </p>
                    </div>

                    {/* LLM Feedback */}
                    <div style={{ marginTop: '0.5rem', borderLeft: '3px solid var(--primary)', paddingLeft: '1rem' }}>
                      <h4 style={{ fontSize: '0.85rem', color: 'var(--primary)', textTransform: 'uppercase', marginBottom: '0.3rem', letterSpacing: '0.05em' }}>
                        AI Interviewer Assessment & Rationale
                      </h4>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        {q.evaluation_feedback || 'No evaluation feedback generated for this question.'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
