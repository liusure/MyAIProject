export default function Home() {
  return (
    <div className="home-page">
      <h1>AI 智能选课推荐系统</h1>
      <p>通过自然语言描述你的选课偏好，AI 为你推荐最优课程方案，自动检测冲突，一键导出 PDF。</p>

      <div className="features">
        <div className="feature-card">
          <h3>自然语言推荐</h3>
          <p>用中文描述你的选课需求，AI 理解你的时间偏好和兴趣方向，智能匹配课程方案。</p>
        </div>
        <div className="feature-card">
          <h3>冲突检测</h3>
          <p>自动检测课程时间重叠、先修课程不满足、校区通勤时间不足等冲突问题。</p>
        </div>
        <div className="feature-card">
          <h3>方案收藏与导出</h3>
          <p>收藏满意的推荐方案，导出 PDF 文件，选课开放时快速对照操作。</p>
        </div>
      </div>
    </div>
  );
}
