import {useState, useRef} from 'react';
import type {
    ImportAnalyzeResponse,
    ImportConfirmResponse,
    ImportError,
    DegradationImpact,
    ColumnMapping,
    MappingResult,
} from '../../types';
import {uploadAnalyze, confirmImport} from '../../services/api';
import {ColumnMappingPreview} from '../ColumnMappingPreview/ColumnMappingPreview';
import './FileUpload.css';

type Step = 'idle' | 'analyzing' | 'preview' | 'importing' | 'done' | 'error';

export function FileUpload() {
    const [step, setStep] = useState<Step>('idle');
    const [analyzeResult, setAnalyzeResult] = useState<ImportAnalyzeResponse | null>(null);
    const [rawData, setRawData] = useState<Record<string, unknown>[]>([]);
    const [confirmResult, setConfirmResult] = useState<ImportConfirmResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [dragOver, setDragOver] = useState(false);
    const [manualMappings, setManualMappings] = useState<ColumnMapping[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFile = async (file: File) => {
        setStep('analyzing');
        setError(null);
        try {
            const result = await uploadAnalyze(file);
            setAnalyzeResult(result);
            setRawData(result.sample_data);
            setStep('preview');
        } catch (e) {
            setError(e instanceof Error ? e.message : '文件分析失败');
            setStep('error');
        }
    };

    const handleConfirm = async () => {
        if (!analyzeResult) return;
        setStep('importing');
        try {
            const mergedMapping: MappingResult = {
                ...analyzeResult.mapping,
                mappings: [...analyzeResult.mapping.mappings, ...manualMappings],
                unmapped_source: analyzeResult.mapping.unmapped_source.filter(
                    (col) => !manualMappings.some((m) => m.source === col)
                ),
                unmapped_target: analyzeResult.mapping.unmapped_target.filter(
                    (t) => !manualMappings.some((m) => m.target === t)
                ),
            };
            const result = await confirmImport(mergedMapping, rawData);
            setConfirmResult(result);
            setStep('done');
        } catch (e) {
            setError(e instanceof Error ? e.message : '导入失败');
            setStep('error');
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) handleFile(file);
    };

    const reset = () => {
        setStep('idle');
        setAnalyzeResult(null);
        setRawData([]);
        setConfirmResult(null);
        setManualMappings([]);
        setError(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const goBackToPreview = () => {
        setStep('preview');
        setConfirmResult(null);
        setError(null);
    };

    if (step === 'analyzing') {
        return (
            <div className="file-upload file-upload--loading">
                <div className="file-upload__spinner"/>
                <p>正在分析文件列名...</p>
            </div>
        );
    }

    if (step === 'preview' && analyzeResult) {
        return (
            <div className="file-upload file-upload--preview">
                <h3>列映射结果</h3>
                <ColumnMappingPreview
                    mapping={analyzeResult.mapping}
                    degradation={analyzeResult.degradation}
                    onManualMappingsChange={setManualMappings}
                />
                <div className="file-upload__actions">
                    <button className="btn btn--primary" onClick={handleConfirm}>
                        确认导入
                    </button>
                    <button className="btn btn--secondary" onClick={reset}>
                        重新选择文件
                    </button>
                </div>
            </div>
        );
    }

    if (step === 'importing') {
        return (
            <div className="file-upload file-upload--loading">
                <div className="file-upload__spinner"/>
                <p>正在导入课程数据...</p>
            </div>
        );
    }

    if (step === 'done' && confirmResult) {
        const hasErrors = confirmResult.errors.length > 0;
        return (
            <div className="file-upload file-upload--done">
                <h3>{hasErrors ? '导入失败' : '导入完成'}</h3>
                {hasErrors ? (
                    <div className="file-upload__errors">
                        <p>以下行导入失败：</p>
                        <ul>
                            {confirmResult.errors.map((err: ImportError, i: number) => (
                                <li key={i}>第 {err.row} 行：{err.message}</li>
                            ))}
                        </ul>
                    </div>
                ) : (
                    <p>成功导入 {confirmResult.total} 条</p>
                )}
                {confirmResult.degradation.missing_fields.length > 0 && (
                    <div className="file-upload__degradation">
                        <p>以下功能因缺少数据而降级：</p>
                        <ul>
                            {confirmResult.degradation.impacts.map((imp: DegradationImpact, i: number) => (
                                <li key={i}>{imp.impact}（{imp.fallback}）</li>
                            ))}
                        </ul>
                    </div>
                )}
                <button className="btn btn--primary" onClick={goBackToPreview}>
                    返回修改映射
                </button>
                <button className="btn btn--secondary" onClick={reset}>
                    重新上传
                </button>
            </div>
        );
    }

    if (step === 'error') {
        return (
            <div className="file-upload file-upload--error">
                <p className="file-upload__error-msg">{error}</p>
                <button className="btn btn--secondary" onClick={reset}>
                    重试
                </button>
            </div>
        );
    }

    return (
        <div
            className={`file-upload ${dragOver ? 'file-upload--drag-over' : ''}`}
            onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
        >
            <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={handleFileSelect}
                style={{display: 'none'}}
            />
            <div className="file-upload__icon">+</div>
            <p className="file-upload__text">拖拽 Excel 文件到此处，或点击选择</p>
            <p className="file-upload__hint">支持 .xlsx / .xls / .csv，最大 5MB</p>
        </div>
    );
}
