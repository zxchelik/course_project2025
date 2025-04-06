import React, {useEffect, useState} from 'react';
import { Layout } from 'antd';
import { Link, Outlet } from 'react-router-dom';
import Header from './Header';
import SideMenu from './SideMenu';

const { Sider, Content } = Layout;

function AppLayout() {
    const [collapsed, setCollapsed] = useState(false);
    const [isManual, setIsManual] = useState(false);

    const toggle = () => {
        setCollapsed(!collapsed);
        setIsManual(true); // ручное действие
    };

    useEffect(() => {
        const handleResize = () => {
            const isMobile = window.innerWidth < 768;

            if (isMobile) {
                setCollapsed(true); // всегда скрываем на телефоне
            } else if (!isManual) {
                setCollapsed(false); // разворачиваем только если не вручную
            }
        };

        handleResize(); // запуск при загрузке

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [isManual]);

    return (
        <Layout style={{ height: '100vh', overflow: 'hidden' }}>
            <Sider
                width={300}
                collapsedWidth={80}
                collapsible
                collapsed={collapsed}
                trigger={null}
                theme="light"
                style={{ overflow: 'hidden', position: 'fixed', height: '100vh', left: 0, top: 0, bottom: 0, zIndex: 100 }}
            >
                <div className="flex flex-col items-center">
                    <Link to="/" className="flex items-center justify-center py-4">
                        <img
                            src= {collapsed ? "/public/static/SPUTNIKAGROLogoSmall.png" : "/public/static/SPUTNIKAGROLogo.png"}
                            alt="Логотип"
                            className="h-12 transition-all duration-300"
                        />
                    </Link>
                    <SideMenu />
                </div>
            </Sider>

            <Layout style={{ marginLeft: collapsed ? 80 : 300, transition: 'margin-left 0.2s ease' }}>
                <Header collapsed={collapsed} onToggle={toggle} />
                <Content
                    style={{
                        height: 'calc(100vh - 64px)',
                        overflowY: 'auto',
                        padding: 24,
                        backgroundColor: '#f9fafb',
                    }}
                >
                    <Outlet />
                </Content>
            </Layout>
        </Layout>
    );
}

export default AppLayout;
