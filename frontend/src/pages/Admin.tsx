import { useState } from 'react';

const API_BASE = 'http://localhost:8000/api/v1';

export default function Admin() {
  const [importResult, setImportResult] = useState<{
    imported: number;
    failed: number;
    errors: Array<{ row: number; message: string }>;
  } | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/admin/courses/import`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || '导入失败');
      setImportResult(data);
    } catch (err) {
      setImportResult({ imported: 0, failed: 0, errors: [{ row: 0, message: String(err) }] });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="admin-page">
      <h1>教务管理</h1>

      <section className="import-section">
        <h2>课程数据导入</h2>
        <p>上传 CSV 或 Excel（.xlsx）课程数据文件，系统将自动识别格式并导入。</p>
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileUpload}
          disabled={uploading}
        />
        {uploading && <p>正在导入...</p>}
        {importResult && (
          <div className="import-result">
            <p>导入成功：{importResult.imported} 条</p>
            <p>导入失败：{importResult.failed} 条</p>
            {importResult.errors.length > 0 && (
              <ul className="import-errors">
                {importResult.errors.map((err, i) => (
                  <li key={i}>
                    第 {err.row} 行：{err.message}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>

      <section className="rules-section">
        <h2>选课规则配置</h2>
        <p>选课规则配置功能开发中...</p>
      </section>
    </div>
  );
}
