import Api from "./api.jsx";

export async function getProducedCount(type, period) {
    const res = await Api.get(`/stats/${type}/produced_count?period=${period}`);
    return res.data;
}

export async function getTopColor() {
    const res = await Api.get(`/stats/container/top_colors`);
    return res.data;
}

export async function getPersonalStats() {
    const tg_id = localStorage.getItem('tg_id');
    const res = await Api.get(`/stats/users/${tg_id}`);
    return res.data;
}