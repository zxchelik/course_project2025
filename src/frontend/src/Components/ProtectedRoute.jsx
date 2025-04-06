import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, allowedRoles = [] }) => {
    // Проверяем, залогинен ли пользователь
    const token = localStorage.getItem('access_token');
    if (!token) {
        // если токена нет – выкидываем на страницу логина
        return <Navigate to="/login" replace />;
    }

    // Если роли не требуются (allowedRoles пуст) – достаточно того, что пользователь авторизован
    if (allowedRoles.length === 0) {
        return children;
    }

    // Смотрим, есть ли у пользователя хоть одна из требуемых ролей
    const roles = JSON.parse(localStorage.getItem('roles')) || [];
    const hasRole = allowedRoles.some((role) => roles.includes(role));

    return hasRole ? children : <Navigate to="/" replace />;
};

export default ProtectedRoute;