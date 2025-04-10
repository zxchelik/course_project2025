import {useEffect, useState} from "react";
import {
    getCassetteNames,
    getCassettes,
    getCassetteStates,
    getCassetteStorages,
    getCassetteTypes,
} from "../../../services/Networking/Inventory.jsx";
import {Table, Tree} from "antd";

const CassetteTable = () => {
    const [data, setData] = useState([]);
    const [states,SetStates] = useState([]);
    const [types,SetTypes] = useState([]);
    const [storages,SetStorages] = useState([]);
    const [names,SetNames] = useState([]);

    useEffect( () => {
        getCassettes().then((res) => {setData(res)}).catch((err) => {console.log(err)});
    },[])
    useEffect( () => {
        getCassetteStates().then((res) => {SetStates(res)}).catch((err) => {console.log(err)});
    },[])
    useEffect( () => {
        getCassetteTypes().then((res) => {SetTypes(res)}).catch((err) => {console.log(err)});
    },[])
    useEffect( () => {
        getCassetteStorages().then((res) => {SetStorages(res)}).catch((err) => {console.log(err)});
    },[])
    useEffect( () => {
        getCassetteNames().then((res) => {SetNames(res)}).catch((err) => {console.log(err)});
    },[])

    const columns = [
        {
            title: 'ID',
            dataIndex: 'id',
            key: 'id',
            sorter: (a, b) => a.id > b.id,
        },
        {
            title: 'Number',
            dataIndex: 'number',      // ⇽ поле «number» приходит в API как batch_number
            key: 'number',
        },
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            sorter: (a, b) => a.name > b.name,
            filters: names,
            filterMode: "tree",
            filterSearch: true,
            onFilter: (value, record) => record.name.indexOf(value) === 0,
        },
        {
            title: 'State',
            dataIndex: 'state',
            key: 'state',
            filters: states,
            filterMode: "tree",
            filterSearch: true,
            onFilter: (value, record) => record.state.indexOf(value) === 0,
        },
        {
            title: 'Type',
            dataIndex: 'type',
            key: 'type',
            filters: types,
            filterMode: "tree",
            filterSearch: true,
            onFilter: (value, record) => record.type.indexOf(value) === 0,
        },
        {
            title: 'Storage',
            dataIndex: 'storage',
            key: 'storage',
            filters: storages,
            filterMode: "tree",
            filterSearch: true,
            onFilter: (value, record) => record.storage.indexOf(value) === 0,
        },
        {
            title: 'Technical comment',
            dataIndex: 'technical_comment',
            key: 'technical_comment',
        },
        {
            title: 'Comment',
            dataIndex: 'comment',
            key: 'comment',
        },
    ]


    return <Table dataSource={data} columns={columns} pagination={{ pageSize: 20, showSizeChanger: true, pageSizeOptions: ['10', '20', '50','100'] }}
    />;
}

export default CassetteTable;