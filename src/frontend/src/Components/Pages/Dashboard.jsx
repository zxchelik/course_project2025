import React, {useEffect, useState, useMemo} from "react";
import {
    Card,
    Spin,
    Button,
    message,
    DatePicker,
    Space,
} from "antd";
import dayjs from "dayjs";
import {getPersonalStats} from "../../services/Networking/stats.jsx";
import {getStatsReport} from "../../services/Networking/Report.jsx";


const Dashboard = () => {

    const [stats, setStats] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);


    const roles = useMemo(() => {
        try {
            const raw = localStorage.getItem("roles");
            return raw ? JSON.parse(raw) : [];
        } catch {
            return [];
        }
    }, []);
    const isAdmin = roles.includes("admin")


    const today = dayjs();
    const [monthYear, setMonthYear] = useState(today); // dayjs instance
    const selectedYear = monthYear.year();
    const selectedMonth = monthYear.month() + 1; // 0‑based => 1‑based


    const [downloading, setDownloading] = useState(false);


    useEffect(() => {
        const loadStats = async () => {
            try {
                const data = await getPersonalStats();
                setStats(data);
            } catch (err) {
                console.error(err);
                setError(err);
            } finally {
                setLoading(false);
            }
        };

        loadStats();
    }, []);


    const handleDownload = async () => {
        setDownloading(true);
        try {
            const blob = await getStatsReport(selectedYear, selectedMonth);
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            const fileName = `${selectedYear}.${String(selectedMonth).padStart(2, "0")}_report.xlsx`;
            link.href = url;
            link.setAttribute("download", fileName);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error(err);
            message.error("Не удалось скачать отчёт");
        } finally {
            setDownloading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[200px] w-full">
                <Spin size="large"/>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-[200px] text-red-500">
                Не удалось загрузить данные: {error.message}
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="grid gap-4 grid-cols-[repeat(auto-fit,minmax(300px,1fr))] auto-rows-[minmax(100px,auto)]">
                {stats.map(({title, info}, idx) => (
                    <Card key={idx} title={title}>
                        {info}
                    </Card>
                ))}
            </div>
            {isAdmin && (
                <Space className="flex justify-end" align="start" wrap>
                    <DatePicker
                        picker="month"
                        allowClear={false}
                        format="MM.YYYY"
                        value={monthYear}
                        onChange={(value) => value && setMonthYear(value)}
                    />

                    <Button
                        type="primary"
                        loading={downloading}
                        onClick={handleDownload}
                    >
                        Скачать отчёт
                    </Button>
                </Space>
            )}
        </div>
    );
};

export default Dashboard;
