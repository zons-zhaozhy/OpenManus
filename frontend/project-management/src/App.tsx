import React from 'react';
import { Layout, Menu, theme } from 'antd';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ProjectList from './pages/ProjectList';
import ProjectDetail from './pages/ProjectDetail';

const { Header, Content, Footer } = Layout;

const App: React.FC = () => {
    const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();

    return (
        <Router>
            <Layout style={{ minHeight: '100vh' }}>
                <Header style={{ display: 'flex', alignItems: 'center' }}>
                    <div className="demo-logo" />
                    <Menu
                        theme="dark"
                        mode="horizontal"
                        defaultSelectedKeys={['1']}
                        items={[
                            {
                                key: '1',
                                label: <Link to="/">项目管理</Link>,
                            },
                        ]}
                        style={{ flex: 1, minWidth: 0 }}
                    />
                </Header>
                <Content style={{ padding: '0 48px' }}>
                    <div
                        style={{
                            background: colorBgContainer,
                            minHeight: 280,
                            padding: 24,
                            borderRadius: borderRadiusLG,
                            marginTop: '24px',
                        }}
                    >
                        <Routes>
                            <Route path="/" element={<ProjectList />} />
                            <Route path="/projects/:id" element={<ProjectDetail />} />
                        </Routes>
                    </div>
                </Content>
                <Footer style={{ textAlign: 'center' }}>
                    OpenManus ©2025 Created by AI
                </Footer>
            </Layout>
        </Router>
    );
};

export default App;
