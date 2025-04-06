import React from 'react';
import {Menu} from 'antd';
import {
    DatabaseFilled, HomeFilled, IdcardFilled
} from '@ant-design/icons';
import {useLocation, useNavigate} from 'react-router-dom';

const SideMenu = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const rolesString = localStorage.getItem('roles');
    const roles = rolesString ? JSON.parse(rolesString) : [];

    const menuItems = [{key: '/', icon: <HomeFilled/>, label: 'Главная'},];
    if (roles.includes('Аналитик') || roles.includes('admin')) {
        menuItems.push({
            key: '/analytics', icon: <IdcardFilled/>, label: 'Аналитика'
        });
    }
    if (roles.includes('Кладовщик') || roles.includes('admin')) {
        menuItems.push({
            key: '/inventory', icon: <DatabaseFilled/>, label: 'Склад'
        });
    }
    if (roles.includes('admin')) {
        menuItems.push({
            key: '/users', icon: <IdcardFilled/>, label: 'Пользователи'
        });
    }
    return (<Menu
            theme="light"
            mode="inline"
            selectedKeys={[location.pathname]}
            onClick={({key}) => navigate(key)}
            items={menuItems}
        />

    );
};

export default SideMenu;
