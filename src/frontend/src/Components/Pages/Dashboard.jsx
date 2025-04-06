import React from 'react';
import {Card, Col, Row} from 'antd';

const Dashboard = () => {
    return (<div className="space-y-6">
        <div className="grid gap-4 grid-cols-[repeat(auto-fit,minmax(300px,1fr))] auto-rows-[minmax(100px,auto)]">
        {/*<div className="grid gap-4 grid-cols-4 auto-rows-[minmax(100px,auto)]">*/}
            <Card title="Изготовленно бочек за месяц">63 шт</Card>
            <Card title="Изготовленно кассет за месяц">63 шт</Card>
            <Card title="Почасовых работ за месяц">63 часа</Card>
            <Card title="Изготовленно кассет за месяц">63 шт</Card>
            <Card title="Дней во компании">63 дня</Card>
            <Card title="Зарплата в этом месяце">63000р</Card>
        </div>
        {/* Тут может быть график и события */}
    </div>);
};

export default Dashboard;
