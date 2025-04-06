import {Card} from "antd";
import React from "react";
import ProducedChartCard from "./ProducedChartCard.jsx";
import ColorPie from "./ColorPie.jsx";

const StatsPage = () => {
    return (<div className="space-y-6">
        <div className="grid gap-4 grid-cols-[repeat(auto-fit,minmax(300px,1fr))] auto-rows-[minmax(100px,auto)]">
            <div className="col-span-2">
                <ProducedChartCard type={"container"}/>
            </div>
            <div className="col-span-2">
                <ProducedChartCard type={"cassette"}/>
            </div>
            <div className="col-span-2 row-span-2">
            <Card title="Популярные цвета"><ColorPie/></Card>
            </div>
        </div>
    </div>);
}

export default StatsPage;