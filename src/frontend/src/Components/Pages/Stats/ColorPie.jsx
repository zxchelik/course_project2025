import {Pie} from "@ant-design/charts";
import {useEffect, useState} from "react";
import {getTopColor} from "../../../services/Networking/stats.jsx";

const ColorPie = () => {
    const [colors,setColors] = useState([])

    useEffect(() => {
        getTopColor().then(r => setColors(r)).catch(err => console.log(err));
    },[])

    const config = {
        data: colors,
        angleField: 'count',
        colorField: 'color',
        innerRadius: 0.6,
        label: {
            text: 'count',
        },
        legend: {
            color: {
                title: false,
                position: 'right',
                rowPadding: 5,
            },
        },

    };
    return <Pie {...config} />;
};
export default ColorPie;