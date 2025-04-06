from src.backend.database.db_cmd.cassette_cmd import get_cassette_info_for_excel
from src.backend.text_templates import exel_header


async def get_all_hw_exel(wb, year, month):
    data: dict = await get_cassette_info_for_excel(month=month, year=year)
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
