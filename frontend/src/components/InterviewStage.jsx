import React, { useState, useEffect, useRef } from 'react';

export default function InterviewStage({ session, onInterviewFinished }) {
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [answer, setAnswer] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingText, setLoadingText] = useState('');
  const [questionCount, setQuestionCount] = useState(0);
  const [maxQuestions] = useState(5);
  const [error, setError] = useState('');
  
  // Feedback state after submitting an answer
  const [feedback, setFeedback] = useState(null);
  const [isDone, setIsDone] = useState(false);

  const hasFetched = useRef(false);

  useEffect(() => {
    if (!hasFetched.current) {
      hasFetched.current = true;
      fetchNextQuestion();
    }
  }, []);

  const fetchNextQuestion = async () => {
    setIsLoading(true);
    setLoadingText('Generating next question...');
    setError('');
    setFeedback(null);
    setAnswer('');

    try {
      const response = await fetch(`/api/sessions/${session.id}/next-question`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        // If 400 it means we finished, check if we should auto-close
        if (response.status === 400) {
          onInterviewFinished();
          return;
        }
        throw new Error(errorData.detail || 'Failed to fetch next question');
      }

      const data = await response.json();
      setCurrentQuestion(data);
      setQuestionCount(prev => prev + 1);
    } catch (err) {
      setError(err.message || 'Error loading question.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInsertCode = () => {
    setAnswer(prev => prev + '\n```javascript\n// Paste or write your code here\n\n```\n');
  };

  const handleSubmitAnswer = async (e) => {
    e.preventDefault();
    if (!answer.trim()) return;

    setIsLoading(true);
    setLoadingText('AI Interviewer is grading your response...');
    setError('');

    try {
      const response = await fetch(`/api/sessions/${session.id}/submit-answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question_id: currentQuestion.id,
          answer_text: answer,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit answer');
      }

      const data = await response.json();
      setFeedback(data);
      setIsDone(data.is_finished);
    } catch (err) {
      setError(err.message || 'Error submitting answer.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEndInterview = async () => {
    if (window.confirm("Are you sure you want to end the interview early? Your responses will be evaluated up to this point.")) {
      setIsLoading(true);
      setLoadingText('Ending session and compiling analytics...');
      try {
        await fetch(`/api/sessions/${session.id}/end`, {
          method: 'POST'
        });
        onInterviewFinished();
      } catch (err) {
        setError('Failed to finalize session.');
        setIsLoading(false);
      }
    }
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s ease', height: '100%' }}>
      {/* Header Info */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <span style={{ 
            fontSize: '0.8rem', 
            fontWeight: 700, 
            textTransform: 'uppercase', 
            background: 'rgba(99, 102, 241, 0.1)', 
            color: 'var(--primary)', 
            padding: '0.3rem 0.8rem', 
            borderRadius: 'var(--radius-full)',
            border: '1px solid rgba(99, 102, 241, 0.2)'
          }}>
            Technical Interview
          </span>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            Active Session 
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontWeight: 'normal' }}>
              ({session.selected_role === 'ai_ml_engineer' ? 'AI/ML Engineer' : session.selected_role === 'backend_engineer' ? 'Backend Engineer' : 'Data Scientist'})
            </span>
          </h2>
        </div>

        <button onClick={handleEndInterview} className="btn btn-secondary" style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}>
          🏳️ Exit & Evaluate Early
        </button>
      </div>

      {/* Progress Stepper */}
      <div className="progress-stepper">
        <span className="step-label">
          Question <strong>{questionCount}</strong> of <strong>{maxQuestions}</strong>
        </span>
        <div className="step-indicator">
          {Array.from({ length: maxQuestions }).map((_, i) => (
            <div 
              key={i} 
              className={`step-dot ${
                i + 1 < questionCount ? 'completed' : i + 1 === questionCount ? 'active' : ''
              }`}
            />
          ))}
        </div>
      </div>

      {/* Split Layout */}
      <div className="layout-split">
        {/* Left Panel: Interviewer Chat */}
        <div className="sidebar-interviewer glass-panel">
          <div className="bot-avatar-container">
            <div className="bot-avatar">🤖</div>
            <div className="bot-info">
              <h3>Aria</h3>
              <p><span className="pulse-dot"></span> Online AI Interviewer</p>
            </div>
          </div>

          <div className="card-chat">
            {currentQuestion && (
              <div className="chat-bubble bot">
                <strong>Question:</strong><br />
                <p style={{ marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>{currentQuestion.question_text}</p>
              </div>
            )}

            {isLoading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', padding: '0.5rem 1rem' }}>
                <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></div>
                <span style={{ fontSize: '0.85rem' }}>{loadingText}</span>
              </div>
            )}

            {feedback && (
              <div style={{ animation: 'fadeIn 0.5s ease' }}>
                <div className="chat-bubble bot" style={{ background: 'rgba(16, 185, 129, 0.08)', borderColor: 'rgba(16, 185, 129, 0.2)', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>Grading Feedback</span>
                    <span style={{ 
                      fontWeight: 800, 
                      fontSize: '1rem',
                      background: 'rgba(16, 185, 129, 0.15)', 
                      padding: '0.1rem 0.5rem', 
                      borderRadius: 'var(--radius-sm)',
                      color: 'var(--accent-emerald)'
                    }}>
                      Score: {feedback.score}/10
                    </span>
                  </div>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {feedback.evaluation_feedback}
                  </p>
                </div>

                {!isLoading && (
                  <button 
                    onClick={isDone ? onInterviewFinished : fetchNextQuestion} 
                    className="btn btn-primary"
                    style={{ width: '100%', padding: '0.8rem' }}
                  >
                    {isDone ? 'Conclude Interview & View Report' : 'Proceed to Next Question ➡️'}
                  </button>
                )}
              </div>
            )}

            {error && (
              <div style={{
                background: 'rgba(244, 63, 94, 0.1)',
                border: '1px solid rgba(244, 63, 94, 0.2)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--accent-rose)',
                padding: '0.8rem',
                fontSize: '0.85rem',
              }}>
                ⚠️ {error}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Workspace Code / Text Editor */}
        <div className="main-editor">
          <div className="workspace-header">
            <div className="workspace-title">
              📟 Workspace Workspace & Editor
            </div>
            <div className="workspace-actions">
              <button onClick={handleInsertCode} className="workspace-btn-action" title="Insert markdown code block">
                {'</> Insert Code'}
              </button>
              <button onClick={() => setAnswer('')} className="workspace-btn-action" disabled={feedback || isLoading}>
                Clear
              </button>
            </div>
          </div>

          <textarea
            className="textarea-editor"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder={`Type your detailed explanation here...\n\nYou can use markdown syntax to structure your answer. If the question asks for code, you can use the "</> Insert Code" button above or type code blocks directly:\n\n\`\`\`python\ndef my_function():\n    return True\n\`\`\``}
            disabled={feedback || isLoading || !currentQuestion}
          />

          <div className="editor-footer">
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Characters: {answer.length} | Markdown Supported
            </span>
            <button 
              onClick={handleSubmitAnswer}
              className="btn btn-primary"
              disabled={!answer.trim() || feedback || isLoading || !currentQuestion}
              style={{ minWidth: '160px' }}
            >
              Submit Answer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
