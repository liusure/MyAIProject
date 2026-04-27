import { useState, useRef, useEffect } from 'react';
import type { ChatMessage } from '../../types';

interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  loading?: boolean;
  emptyResults?: boolean;
  streamingContent?: string;
}

export default function ChatPanel({ messages, onSend, loading, emptyResults, streamingContent }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput('');
  };

  return (
    <div className="chat-panel">
      <div className="chat-messages">
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
        {loading && !streamingContent && (
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
