import { Tabs } from 'antd';
import ContainerTable from "./ContainerTable.jsx";
import PlasticTable from "./PlascticTable.jsx";
import CassetteTable from "./CassetteTable.jsx";

/**
 * Компонент «Страница складского учёта»
 */
export default function InventoryPage() {
    const onChange = key => {
        console.log(key);
    };
    const items = [
        {
            key: '1',
            label: 'Бочки',
            children: <ContainerTable/>,
        },
        {
            key: '3',
            label: 'Пластик',
            children: <PlasticTable/>,
        },
        {
            key: '2',
            label: 'Кассеты',
            children: <CassetteTable/>,
        },
    ];

    return (
        <Tabs centered={true} defaultActiveKey="1" items={items} onChange={onChange} />
    );
}
