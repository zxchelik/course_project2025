import Api from "./api.jsx";

export async function getStatsReport(year, month) {
    const res = await Api.get(`/stats/report?year=${year}&month=${month}`, { responseType: 'blob' });
    return res.data;           // Blob
}