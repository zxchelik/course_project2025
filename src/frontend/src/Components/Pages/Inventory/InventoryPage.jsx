import { Tabs } from 'antd';
import ContainerTable from "./ContainerTable.jsx";
import PlascticTable from "./PlascticTable.jsx";

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
            children: <PlascticTable/>,
        },
        {
            key: '2',
            label: 'Кассеты',
            children: 'Content of Tab Pane 2',
        },
    ];

    return (
        <Tabs centered={true} defaultActiveKey="1" items={items} onChange={onChange} />
    );
}
