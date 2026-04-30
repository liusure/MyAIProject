import { useState, useRef, useEffect, useCallback } from 'react';
import type { ChatMessage, RecommendationProgress } from '../../types';

interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  loading?: boolean;
  emptyResults?: boolean;
  streamingContent?: string;
  progressMessages?: RecommendationProgress[];
}

export default function ChatPanel({ messages, onSend, loading, emptyResults, streamingContent, progressMessages }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const [isAutoScroll, setIsAutoScroll] = useState(true);
  const [hasNewMessages, setHasNewMessages] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatMessagesRef = useRef<HTMLDivElement>(null);

  // IntersectionObserver: detect if bottom sentinel is visible
  useEffect(() => {
    const el = messagesEndRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsAutoScroll(true);
          setHasNewMessages(false);
        } else {
          setIsAutoScroll(false);
        }
      },
      { root: chatMessagesRef.current, threshold: 0.1 },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Auto-scroll when new content arrives and user is at bottom
  useEffect(() => {
    if (isAutoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      setHasNewMessages(false);
    } else if (streamingContent || (progressMessages && progressMessages.length > 0)) {
      setHasNewMessages(true);
    }
  }, [messages, streamingContent, progressMessages, isAutoScroll]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    setIsAutoScroll(true);
    setHasNewMessages(false);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput('');
    // Ensure auto-scroll resumes when user sends a message
    setIsAutoScroll(true);
    setHasNewMessages(false);
  };

  return (
    <div className="chat-panel">
      <div className="chat-messages" ref={chatMessagesRef}>
        {messages.length === 0 && !loading && (
          <div style={{ textAlign: 'center', padding: 'var(--spacing-xl)', color: 'var(--color-text-light)' }}>
            <p>描述你的选课偏好，我来帮你推荐课程方案</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-content">{msg.content}</div>
            {msg.degraded && (
              <div className="degraded-notice">LLM 服务不可用，已切换至关键词搜索</div>
            )}
          </div>
        ))}
        {progressMessages && progressMessages.length > 0 && (
          <div className="message assistant" style={{ opacity: 0.8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
              <div
                style={{
                  width: 14,
                  height: 14,
                  border: '2px solid var(--color-border)',
                  borderTop: '2px solid var(--color-primary)',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                  flexShrink: 0,
                }}
              />
              <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.92em' }}>
                {progressMessages[progressMessages.length - 1].message}
              </span>
            </div>
          </div>
        )}
        {streamingContent && (
          <div className="message assistant">
            <div className="message-content">
              {streamingContent}
              <span
                style={{
                  display: 'inline-block',
                  width: 2,
                  height: 14,
                  backgroundColor: 'var(--color-primary)',
                  marginLeft: 2,
                  animation: 'blink 1s step-end infinite',
                  verticalAlign: 'text-bottom',
                }}
              />
            </div>
          </div>
        )}
        {loading && !streamingContent && !(progressMessages && progressMessages.length > 0) && (
          <div className="message assistant">
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
              <div
                style={{
                  width: 16,
                  height: 16,
                  border: '2px solid var(--color-border)',
                  borderTop: '2px solid var(--color-primary)',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                }}
              />
              <span style={{ color: 'var(--color-text-secondary)' }}>加载中...</span>
            </div>
          </div>
        )}
        {emptyResults && !loading && (
          <div
            style={{
              textAlign: 'center',
              padding: 'var(--spacing-lg)',
              color: 'var(--color-text-light)',
              backgroundColor: 'var(--color-bg)',
              borderRadius: 'var(--radius-sm)',
              margin: 'var(--spacing-sm)',
            }}
          >
            无结果
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* "有新消息" floating button */}
      {hasNewMessages && !isAutoScroll && (
        <div
          style={{
            position: 'absolute',
            bottom: '70px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 10,
          }}
        >
          <button
            onClick={scrollToBottom}
            style={{
              padding: '6px 16px',
              borderRadius: '20px',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-primary)',
              fontSize: '0.85em',
              cursor: 'pointer',
              boxShadow: 'var(--shadow-hover)',
              transition: 'var(--transition-fast)',
            }}
          >
            ↓ 有新消息
          </button>
        </div>
      )}

      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="描述你的选课偏好，如：我想选周三下午的计算机课程"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          发送
        </button>
      </form>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes blink {
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
