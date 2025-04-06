import Api from "./api.jsx";

export async function getContainers() {
    const res = await Api.get('/inventory/containers');
    return res.data;
}
export async function getContainersStorages() {
    const res = await Api.get('/inventory/containers/storages');
    return res.data.map(storage => ({text:storage, value: storage}));
}

export async function getContainersNames() {
    const res = await Api.get('/inventory/containers/names');
    return res.data.children;
}

export async function getPlastic() {
    const res = await Api.get('/inventory/plastic');
    return res.data;
}