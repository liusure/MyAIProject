import { useRef, useState, useEffect, useCallback } from 'react';
import { toPng } from 'html-to-image';
import ScheduleView from '../ScheduleView/ScheduleView';
import type { ScheduleSlot } from '../../types';
import './ScheduleModal.css';

interface ScheduleCourse {
  id: string;
  name: string;
  instructor?: string | null;
  location?: string | null;
  schedule: ScheduleSlot[];
}

interface ScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  courses: ScheduleCourse[];
  planName: string;
}

export default function ScheduleModal({ isOpen, onClose, courses, planName }: ScheduleModalProps) {
  const contentRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleKeyDown]);

  const handleExport = async () => {
    if (!contentRef.current) return;
    setExporting(true);
    setError(null);
    try {
      const dataUrl = await toPng(contentRef.current, { pixelRatio: 2 });
      const a = document.createElement('a');
      a.href = dataUrl;
      a.download = `${planName}-课程表.png`;
      a.click();
    } catch {
      setError('图片导出失败，请尝试截图保存。');
    } finally {
      setExporting(false);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="schedule-modal-overlay" onClick={handleOverlayClick}>
      <div className="schedule-modal-container">
        <div className="schedule-modal-header">
          <h3>{planName} — 课程表</h3>
          <div className="schedule-modal-actions">
            <button
              className="schedule-modal-export-btn"
              onClick={handleExport}
              disabled={exporting}
            >
              {exporting ? '导出中...' : '导出图片'}
            </button>
            <button className="schedule-modal-close-btn" onClick={onClose}>
              &times;
            </button>
          </div>
        </div>
        {error && <div className="schedule-modal-error">{error}</div>}
        <div className="schedule-modal-content" ref={contentRef}>
          <ScheduleView courses={courses} />
        </div>
      </div>
    </div>
  );
}
