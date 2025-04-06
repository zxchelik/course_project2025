import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from '../Components/Pages/AuthPage.jsx';
import Dashboard from '../Components/Pages/Dashboard.jsx';
import ProtectedRoute from '../Components/ProtectedRoute';
import AppLayout from '../Components/Layout.jsx';
import UserTable from "../Components/Pages/UserTable.jsx";
import InventoryPage from "../Components/Pages/Inventory/InventoryPage.jsx";
import StatsPage from "../Components/Pages/Stats/StatsPage.jsx";
// import AnalyticsPage from "../Components/AnalyticsPage.jsx"; // Например

const AppRoutes = () => (
    <Routes>
        <Route path="/login" element={<AuthPage />} />

        {/* Всё остальное — защищённое */}
        <Route
            path="/*"
            element={
                <ProtectedRoute>
                    <AppLayout />
                </ProtectedRoute>
            }
        >
            {/* Обычная страница, достаточно быть авторизованным */}
            <Route index element={<Dashboard />} />

            {/* Доступно только пользователям, у которых роль 'Аналитик' или 'admin' */}
            <Route
                path="analytics"
                element={
                    <ProtectedRoute allowedRoles={['Аналитик', 'admin']}>
                        <StatsPage/>
                    </ProtectedRoute>
                }
            />
            <Route
                path="inventory"
                element={
                    <ProtectedRoute allowedRoles={['Кладовщик', 'admin']}>
                        <InventoryPage />
                    </ProtectedRoute>
                }
            />

            {/* Доступно только admin */}
            <Route
                path="users"
                element={
                    <ProtectedRoute allowedRoles={['admin']}>
                        <UserTable />
                    </ProtectedRoute>
                }
            />

            {/* Дополнительно можно делать другие защищённые пути */}
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
);

export default AppRoutes;
