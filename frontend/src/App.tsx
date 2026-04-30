import {BrowserRouter, Routes, Route, Link, useLocation, Outlet} from 'react-router-dom';
import Home from './pages/Home';
import CourseSelect from './pages/CourseSelect';
import MyPlans from './pages/MyPlans';
import './App.css';

function AppLayout() {
    const location = useLocation();

    return (
        <>
            <nav>
                <Link to="/">首页</Link>
                <Link to="/select">智能选课</Link>
                <Link to="/plans">我的方案</Link>
                <a className="nav-download" href="/2026年春季学期课表.xlsx" download>下载示例数据</a>
            </nav>
            <main>
                <div style={{display: location.pathname === '/select' ? 'block' : 'none'}}>
                    <CourseSelect/>
                </div>
                <div style={{display: location.pathname === '/plans' ? 'block' : 'none'}}>
                    <MyPlans/>
                </div>
                <Outlet/>
            </main>
        </>
    );
}

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route element={<AppLayout/>}>
                    <Route path="/" element={<Home/>}/>
                    <Route path="/select" element={null}/>
                    <Route path="/plans" element={null}/>
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;
