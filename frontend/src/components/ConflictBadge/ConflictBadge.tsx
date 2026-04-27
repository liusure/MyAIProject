import type { Conflict } from '../../types';

interface ConflictBadgeProps {
  conflict: Conflict;
}

const CONFLICT_LABELS: Record<string, string> = {
  time: '时间冲突',
  location: '地点冲突',
  prerequisite: '先修不足',
  commute: '通勤冲突',
};

const SEVERITY_STYLES: Record<string, { color: string; bg: string }> = {
  error: { color: 'var(--color-danger)', bg: 'var(--color-danger-bg)' },
  warning: { color: 'var(--color-warning)', bg: 'var(--color-warning-bg)' },
};

export default function ConflictBadge({ conflict }: ConflictBadgeProps) {
  const style = SEVERITY_STYLES[conflict.severity] || SEVERITY_STYLES.warning;

  return (
    <div
      className={`conflict-badge ${conflict.severity}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 'var(--spacing-xs)',
        padding: '4px 10px',
        borderRadius: 'var(--radius-sm)',
        backgroundColor: style.bg,
        color: style.color,
        border: `1px solid ${style.color}`,
        fontSize: '0.85em',
        transition: 'var(--transition-fast)',
      }}
    >
      <span className="conflict-type" style={{ fontWeight: 600 }}>
        {CONFLICT_LABELS[conflict.type] || conflict.type}
      </span>
      <span className="conflict-message">{conflict.message}</span>
    </div>
  );
}
