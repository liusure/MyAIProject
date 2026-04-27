import { useState } from 'react';
import type { Course } from '../../types';
import './PlanActions.css';

interface PlanActionsProps {
  courses: Course[];
  isFavorited: boolean;
  onToggleFavorite: () => void;
}

export default function PlanActions({ courses, isFavorited, onToggleFavorite }: PlanActionsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const text = courses
      .map((c) => (c.course_no ? `${c.name}（${c.course_no}）` : c.name))
      .join('\n');

    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="plan-actions">
      <button
        className={`plan-action-btn favorite-btn${isFavorited ? ' favorited' : ''}`}
        onClick={onToggleFavorite}
        title={isFavorited ? '取消收藏' : '收藏方案'}
      >
        {isFavorited ? '★' : '☆'}
      </button>
      <button
        className={`plan-action-btn copy-btn${copied ? ' copied' : ''}`}
        onClick={handleCopy}
        title={copied ? '已复制' : '复制课程信息'}
        disabled={courses.length === 0}
      >
        {copied ? '已复制' : '复制'}
      </button>
    </div>
  );
}
