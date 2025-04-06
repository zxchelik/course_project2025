import React from 'react';

import {Button, Spin} from 'antd';
import {Link} from 'react-router-dom';
import {LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined} from "@ant-design/icons";

function Header({collapsed, onToggle}) {
    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
    };
    const user = localStorage.getItem('user');

    return (<header className="bg-white shadow p-4 flex justify-between items-center">
        <div className="flex items-center space-x-3">
            <Button
                type="text"
                icon={collapsed ? <MenuUnfoldOutlined/> : <MenuFoldOutlined/>}
                onClick={onToggle}
            />

        </div>

        <nav className="flex items-center space-x-6">
            <div className="flex items-center space-x-4">
                <span className="text-gray-700">{user}</span>
                <Button
                    variant="solid"
                    color="danger"
                    size="default"
                    icon={<LogoutOutlined/>}
                    onClick={handleLogout}
                />
            </div>
        </nav>
    </header>);
}

export default Header;
