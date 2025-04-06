import React, {useState} from 'react';
import {Tabs, Form, Input, Button, message} from 'antd';
import {useNavigate} from 'react-router-dom';
import Api from "../../services/Networking/api.jsx";
import {jwtDecode} from "jwt-decode";


const AuthPage = () => {
    const [loading, setLoading] = useState(false);
    const [messageApi, contextHolder] = message.useMessage();
    const navigate = useNavigate();

    const handleLogin = async (values) => {
        setLoading(true);
        try {
            const formData = new URLSearchParams(values);
            const response = await Api.post('/auth/login', formData, {headers: {'Content-Type': 'application/x-www-form-urlencoded'}});
            localStorage.setItem('access_token', response.data.access_token);
            localStorage.setItem('user', `${response.data.user.fio} (${response.data.user.tg_id})`);
            const decoded = jwtDecode(response.data.access_token);
            localStorage.setItem('roles', JSON.stringify(decoded.roles || []))
            navigate('/');
        } catch (error) {
            messageApi.error(error.response?.data.detail || 'Ошибка при входе');
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (values) => {
        setLoading(true);
        try {
            const response = await Api.post('/auth/register', {
                tg_id: Number(values.tg_id), user_login: values.user_login, password: values.password,
            });
            messageApi.success('Регистрация прошла успешно!');
            localStorage.setItem('access_token', response.data.access_token);
            localStorage.setItem('user', `${response.data.user.fio} (${response.data.user.tg_id})`);
            const decoded = jwtDecode(response.data.access_token);
            localStorage.setItem('roles', JSON.stringify(decoded.roles || []))
            navigate('/');
        } catch (error) {
            messageApi.error(error.response?.data.detail || 'Ошибка при регистрации');
        } finally {
            setLoading(false);
        }
    };

    return (<div className="min-h-screen flex items-center justify-center bg-gray-100">
        {contextHolder}
        <div className="bg-white p-8 rounded shadow-md w-full max-w-md">
            <Tabs
                defaultActiveKey="login"
                items={[{
                    key: 'login', label: 'Вход', children: (<Form layout="vertical" onFinish={handleLogin}>
                        <Form.Item name="username" label="Логин" rules={[{required: true}]}>
                            <Input placeholder="Введите логин"/>
                        </Form.Item>
                        <Form.Item name="password" label="Пароль" rules={[{required: true}]}>
                            <Input.Password placeholder="Введите пароль"/>
                        </Form.Item>
                        <Button type="primary" htmlType="submit" loading={loading} block>
                            Войти
                        </Button>
                    </Form>),
                }, {
                    key: 'register', label: 'Регистрация', children: (<Form layout="vertical" onFinish={handleRegister}>
                        <Form.Item name="tg_id" label="Telegram ID" rules={[{required: true}]}>
                            <Input placeholder="Введите ID можно узнать введя в бота '/id'"/>
                        </Form.Item>
                        <Form.Item name="user_login" label="Логин" rules={[{required: true}]}>
                            <Input placeholder="Введите логин"/>
                        </Form.Item>
                        <Form.Item name="password" label="Пароль" rules={[{required: true}]}>
                            <Input.Password placeholder="Введите пароль"/>
                        </Form.Item>
                        <Button type="primary" htmlType="submit" loading={loading} block>
                            Зарегистрироваться
                        </Button>
                    </Form>),
                },]}
            />
        </div>
    </div>);
};

export default AuthPage;
