import openpyxl
from openpyxl.worksheet.worksheet import Worksheet


def load_ral() -> dict[int, list[int]]:
    wb = openpyxl.load_workbook("RAL.xlsx")
    sheet: Worksheet = wb['RAL']
    data = sheet.values
    ral = {}
    for row in data:
        ral_id, rgb, name = row
        ral[ral_id] = [int(i) for i in rgb.split(',')]
    return ral


if __name__ == '__main__':
    print(load_ral())
