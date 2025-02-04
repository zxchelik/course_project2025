from openpyxl import Workbook

from database.db_cmd.cantainers_cmd import get_all_container_by_month
from text_templates import exel_header


async def get_all_container_exel(wb: Workbook, year, month):
    data: dict = await get_all_container_by_month(year=year, month=month)
    for index, l in enumerate(data.items()):
        user, info_list = l
        info_list.sort()
        info_list.append([None, None, None, None])
        try:
            ws = wb[user]
        except KeyError:
            ws = wb.create_sheet(user)
            header = exel_header
            ws.append(header)

        last_date, last_name, number, count_percent = info_list[0]
        count = 1

        number_list = [number]
        for info in info_list[1:]:
            date_, name, number, percent = info
            if date_ == last_date and name == last_name:
                count_percent += percent
                count += 1
                number_list.append(number)
            else:
                ws.append([last_date, ", ".join(number_list), last_name, count, count_percent])
                count = 1
                count_percent = percent
                last_date = date_
                last_name = name
                number_list = [number]
