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
// 👉 Кассеты -----------------------------------------------------
/** GET /inventory/cassette */
export async function getCassettes() {
    const res = await Api.get('/inventory/cassette');
    return res.data;
}

/** GET /inventory/cassette/states */
export async function getCassetteStates() {
    const res = await Api.get('/inventory/cassette/states');
    return res.data.map(item => ({text:item, value: item}));
}

/** GET /inventory/cassette/types */
export async function getCassetteTypes() {
    const res = await Api.get('/inventory/cassette/types');
    return res.data.map(item => ({text:item, value: item}));
}

/** GET /inventory/cassette/storages */
export async function getCassetteStorages() {
    const res = await Api.get('/inventory/cassette/storages');
    return res.data.map(item => ({text:item, value: item}));
}

/** GET /inventory/cassette/names */
export async function getCassetteNames() {
    const res = await Api.get('/inventory/cassette/names');
    return res.data.map(item => ({text:item, value: item}));
}