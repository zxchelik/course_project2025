from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet


def auto_size_excel(ws: Worksheet):
    for column_cells in ws.columns:
        new_column_length = max(len(str(cell.value)) for cell in column_cells)
        new_column_letter = get_column_letter(column_cells[0].column)
        if new_column_length > 0:
            ws.column_dimensions[new_column_letter].width = new_column_length * 1.1
