import Api from "./api.jsx";

export async function getProducedCount(type, period) {
    const res = await Api.get(`/stats/${type}/produced_count?period=${period}`);
    return res.data;
}

export async function getTopColor() {
    const res = await Api.get(`/stats/container/top_colors`);
    return res.data;
}