import {Card, Select} from 'antd'
import {Line} from '@ant-design/charts'
import {useEffect, useState} from 'react'
import {getProducedCount} from "../../../services/Networking/stats.jsx";

const {Option} = Select

const ProducedChartCard = ({type}) => {
    const [data, setData] = useState([])
    const [period, setPeriod] = useState('week')
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        setLoading(true)
        getProducedCount(type, period).then(data => {
            setData(data)
        }).catch(error => {
            console.log(error)
        }).finally(() => setLoading(false))
    }, [period, type])

    return (<Card
            title="Произведено продукции"
            extra={<Select
                value={period}
                onChange={setPeriod}
                style={{width: '100%'}}
                size="small"
            >
                <Option value="week">Неделя</Option>
                <Option value="month">Месяц</Option>
                <Option value="all">Всё время</Option>
            </Select>}
            loading={loading}
        >
            <Line
                data={data}
                xField="produced_date"
                yField="count"
                smooth
                animation={true}
                height={300}
                xAxis={{label: {autoHide: true, autoRotate: false}}}
                scrollbar={period === "all"?{x: {ratio: 0.4},}:{}}
            />
        </Card>)
}

export default ProducedChartCard
