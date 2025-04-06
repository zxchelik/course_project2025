import {useEffect, useState} from "react";
import {getContainers, getContainersNames, getContainersStorages} from "../../../services/Networking/Inventory.jsx";
import {Table, Tree} from "antd";

const ContainerTable = () => {
    const [data, setData] = useState([]);
    const [storages, setStorages] = useState([]);
    const [names, setNames] = useState([]);
    useEffect( () => {
        getContainers().then((res) => {setData(res)}).catch((err) => {console.log(err)});
    },[])
    useEffect(() => {
        getContainersStorages().then((res) => {setStorages(res)}).catch((err) => {console.log(err)});
    },[])
    useEffect(() => {
        getContainersNames().then((res) => {setNames(res)}).catch((err) => {console.log(err)});
    },[])
    const columns = [
        {
            title: 'Number',
            dataIndex: 'number',
            key: 'number',
            sorter: (a, b) => a.number > b.number,
        },
        {
            title: 'Date',
            dataIndex: 'date_cont',
            key: 'date_cont',
            sorter: (a, b) => a.date_cont > b.date_cont,
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
            title: 'Color',
            dataIndex: 'color',
            key: 'color',
            sorter: (a, b) => Number(a.color) > Number(b.color),
        },
        {
            title: 'Weight',
            dataIndex: 'weight',
            key: 'weight',
            sorter: (a, b) => Number(a.weight) > Number(b.weight),

        },
        {
            title: 'Batch number',
            dataIndex: 'batch_number',
            key: 'batch_number',
        },
        {
            title: 'Cover article',
            dataIndex: 'cover_article',
            key: 'cover_article',
        },
        {
            title: 'Comments',
            dataIndex: 'comments',
            key: 'comments',
        },
        {
            title: 'Storage',
            dataIndex: 'storage',
            key: 'storage',
            sorter: (a, b) => a.storage > b.storage,
            filters: storages,
            filterSearch: true,
            onFilter: (value, record) => record.storage.indexOf(value) === 0,
        },
    ];


    return <Table dataSource={data} columns={columns} pagination={{ pageSize: 20, showSizeChanger: true, pageSizeOptions: ['10', '20', '50','100'] }}
    />;
}

export default ContainerTable;