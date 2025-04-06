import axios from 'axios';

const Api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Добавляем access_token в каждый запрос
Api.interceptors.request.use(config => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Ловим 401
Api.interceptors.response.use(
    response => response,
    error => {

        if (error.response?.status === 401) {
            const token = localStorage.getItem('access_token');
            if (token) {
                // удаляем токен
                localStorage.removeItem('access_token');
                localStorage.removeItem('user');
                // редиректим
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default Api;
