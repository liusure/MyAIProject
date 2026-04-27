import { useState, useEffect, useCallback } from 'react';
import type { MappingResult, DegradationReport, ColumnMapping } from '../../types';
import './ColumnMappingPreview.css';

const SYSTEM_FIELDS: { key: string; label: string; isRequired: boolean }[] = [
  { key: 'name', label: '课程名称', isRequired: true },
  { key: 'credit', label: '学分', isRequired: true },
  { key: 'course_no', label: '课程编号', isRequired: false },
  { key: 'instructor', label: '授课教师', isRequired: false },
  { key: 'capacity', label: '容量', isRequired: false },
  { key: 'location', label: '上课地点', isRequired: false },
  { key: 'campus', label: '校区', isRequired: false },
  { key: 'category', label: '分类', isRequired: false },
  { key: 'semester', label: '学期', isRequired: false },
  { key: 'schedule', label: '上课时间', isRequired: false },
];

const FIELD_DESCRIPTIONS: Record<string, string> = {
  name: '用于识别和展示课程',
  credit: '用于学分统计和毕业要求计算',
  course_no: '用于精确匹配和去重课程',
  instructor: '用于按教师筛选和推荐课程',
  capacity: '用于显示选课人数上限',
  location: '用于显示上课地点',
  campus: '用于检测跨校区通勤冲突',
  category: '用于按分类筛选课程',
  semester: '用于按学期筛选课程',
  schedule: '用于检测课程时间冲突',
};

interface ColumnMappingPreviewProps {
  mapping: MappingResult;
  degradation: DegradationReport;
  onManualMappingsChange?: (mappings: ColumnMapping[]) => void;
}

export function ColumnMappingPreview({ mapping, degradation, onManualMappingsChange }: ColumnMappingPreviewProps) {
  const [manualSelections, setManualSelections] = useState<Record<string, string>>({});

  const mappedTargets = new Set(mapping.mappings.map((m) => m.target));

  const degradationMap = new Map(
    degradation.impacts.map((imp) => [imp.field, imp])
  );

  const unmappedTargets = SYSTEM_FIELDS.filter((f) => !mappedTargets.has(f.key));

  const availableColumns = useCallback(
    (currentTarget: string) => {
      const selectedByOthers = new Set(
        Object.entries(manualSelections)
          .filter(([target, col]) => target !== currentTarget && col !== '')
          .map(([, col]) => col)
      );
      return mapping.unmapped_source.filter((col) => !selectedByOthers.has(col));
    },
    [manualSelections, mapping.unmapped_source]
  );

  useEffect(() => {
    if (!onManualMappingsChange) return;
    const manualMappings: ColumnMapping[] = Object.entries(manualSelections)
      .filter(([, source]) => source !== '')
      .map(([target, source]) => ({ source, target, confidence: 1.0 }));
    onManualMappingsChange(manualMappings);
  }, [manualSelections, onManualMappingsChange]);

  const handleSelect = (target: string, source: string) => {
    setManualSelections((prev) => ({ ...prev, [target]: source }));
  };

  return (
    <div className="column-mapping-preview">
      <div className="mapping-section">
        <h4>已识别的列映射</h4>
        <table className="mapping-table">
          <thead>
            <tr>
              <th>原始列名</th>
              <th>→</th>
              <th>系统字段</th>
              <th>置信度</th>
            </tr>
          </thead>
          <tbody>
            {mapping.mappings.map((m: ColumnMapping, i: number) => (
              <tr key={i}>
                <td>{m.source}</td>
                <td className="mapping-arrow">→</td>
                <td>{SYSTEM_FIELDS.find((f) => f.key === m.target)?.label || m.target}</td>
                <td>
                  <span className={`confidence confidence--${m.confidence >= 0.9 ? 'high' : m.confidence >= 0.7 ? 'medium' : 'low'}`}>
                    {Math.round(m.confidence * 100)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {unmappedTargets.length > 0 ? (
        <div className="mapping-section mapping-section--unmapped">
          <h4>未识别的系统字段（可从文件列中选择映射，不选择则忽略）</h4>
          <div className="unmapped-list">
            {unmappedTargets.map((field) => {
              const deg = degradationMap.get(field.key);
              return (
                <div key={field.key} className={`unmapped-item ${field.isRequired ? 'unmapped-item--required' : ''}`}>
                  <span className={`unmapped-field-label ${field.isRequired ? 'unmapped-field-label--required' : ''}`}>
                    {field.label}
                    {field.isRequired && <span className="required-badge">必填</span>}
                  </span>
                  <div className="field-info">
                    <span className="field-description">{FIELD_DESCRIPTIONS[field.key]}</span>
                    {deg && (
                      <span className="field-degradation">
                        未映射影响：{deg.impact}（{deg.fallback}）
                      </span>
                    )}
                  </div>
                  <select
                    className="unmapped-select"
                    value={manualSelections[field.key] || ''}
                    onChange={(e) => handleSelect(field.key, e.target.value)}
                  >
                    <option value="">不映射</option>
                    {availableColumns(field.key).map((col) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="mapping-section mapping-section--success">
          <p className="success-message">所有字段已成功识别</p>
        </div>
      )}
    </div>
  );
}
