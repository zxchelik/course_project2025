from src.backend.database.db_cmd.hourly_work_cmd import get_all_hourly_work_by_month
from src.backend.text_templates import exel_header


async def get_all_hw_exel(wb, year, month):
    data: dict = await get_all_hourly_work_by_month(month=month, year=year)
    for index, l in enumerate(data.items()):
        user_fio, info_list = l
        info_list.sort()

        try:
            ws = wb[user_fio]
        except KeyError:
            ws = wb.create_sheet(user_fio)
            header = exel_header
            ws.append(header)

        for info in info_list:
            ws.append(info)
