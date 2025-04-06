import {useEffect, useState} from "react";
import {
    getPlastic
} from "../../../services/Networking/Inventory.jsx";
import {Table} from "antd";

const PlasticTable = () => {
    const [data, setData] = useState([]);
    useEffect( () => {
        getPlastic().then((res) => {setData(res)}).catch((err) => {console.log(err)});
    },[])
    const columns = [
        {
            title: 'Номер цвета',
            dataIndex: 'color',
            key: 'color',
            sorter: (a, b) => Number(a.color) > Number(b.color),

        },
        {
            title: 'Осталось (кг)',
            dataIndex: 'total_weight',
            key: 'total_weight',
            sorter: (a, b) => Number(a.total_weight) > Number(b.total_weight),
        }
    ];


    return <Table dataSource={data} columns={columns} pagination={false}
    />;
}

export default PlasticTable;