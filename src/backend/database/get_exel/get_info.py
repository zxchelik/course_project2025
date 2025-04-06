from typing import Callable, Awaitable

from openpyxl.workbook import Workbook

from src.backend.text_templates import exel_header


async def write_info_to_excel_file(
    wb: Workbook, year: int, month: int, get_info_func: Callable[..., Awaitable[dict[str, list]]]
):
    """

    :param wb: WorkBook
    :param year: Год (например, 2025)
    :param month: Номер месяца (1-12)
    :param get_info_func: Принимает kwargs(month, year) -> dict[user_fio: list[data]]
    """
    data = await get_info_func(month=month, year=year)
    for index, l in enumerate(data.items()):
        user_fio, info_list = l

        try:
            ws = wb[user_fio]
        except KeyError:
            ws = wb.create_sheet(user_fio)
            header = exel_header
            ws.append(header)

        for info in info_list:
            ws.append(info)
