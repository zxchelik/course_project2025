from openpyxl import Workbook

from database.get_exel.get_container import get_all_container_exel
from database.get_exel.get_hourly_work import get_all_hw_exel


async def get_full_exel(year, month):
    wb = Workbook()
    del wb['Sheet']
    await get_all_container_exel(wb=wb, year=year, month=month)
    await get_all_hw_exel(wb=wb, year=year, month=month)
    file_name = f"{year:0>2}.{month:0>2} тест.xlsx"
    wb.save(file_name)
    return file_name
