import asyncio
from io import BytesIO

from openpyxl import Workbook

from database.db_cmd.cassette_cmd import (
    get_cassette_info_func_generator,
    get_cassette_cutting_for_excel,
    get_cassette_painting_for_excel,
)
from database.db_cmd.hourly_work_cmd import get_all_hourly_work_by_month
from database.get_exel.get_container import get_all_container_exel
from database.get_exel.get_info import write_info_to_excel_file


async def get_full_exel(year, month):
    wb = Workbook()
    del wb["Sheet"]
    await get_all_container_exel(wb=wb, year=year, month=month)
    # await get_all_hw_exel(wb=wb, year=year, month=month)
    await write_info_to_excel_file(wb=wb, year=year, month=month, get_info_func=get_all_hourly_work_by_month)
    await write_info_to_excel_file(wb=wb, year=year, month=month, get_info_func=get_cassette_cutting_for_excel)
    await write_info_to_excel_file(
        wb=wb, year=year, month=month, get_info_func=get_cassette_info_func_generator(cassette_state=2)
    )
    await write_info_to_excel_file(wb=wb, year=year, month=month, get_info_func=get_cassette_painting_for_excel)
    file_name = f"{year:0>2}.{month:0>2} тест.xlsx"
    wb.save(file_name)
    return file_name


async def get_full_exel_to_stream(year, month) -> BytesIO:
    wb = Workbook()
    del wb["Sheet"]

    await get_all_container_exel(wb=wb, year=year, month=month)
    # await get_all_hw_exel(wb=wb, year=year, month=month)
    await write_info_to_excel_file(wb=wb, year=year, month=month, get_info_func=get_all_hourly_work_by_month)
    await write_info_to_excel_file(wb=wb, year=year, month=month, get_info_func=get_cassette_cutting_for_excel)
    await write_info_to_excel_file(
        wb=wb, year=year, month=month, get_info_func=get_cassette_info_func_generator(cassette_state=2)
    )
    await write_info_to_excel_file(wb=wb, year=year, month=month, get_info_func=get_cassette_painting_for_excel)

    stream = BytesIO()
    wb.save(stream)  # пишем прямо в поток
    stream.seek(0)  # обязательно в начало
    return stream


if __name__ == "__main__":
    asyncio.run(get_full_exel(2025, 3))
