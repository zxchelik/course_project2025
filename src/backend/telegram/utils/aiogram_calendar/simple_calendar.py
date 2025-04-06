import calendar
from datetime import datetime, timedelta, date

from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# setting callback_data prefix and parts
calendar_callback_filter = F.data.startswith("simple_calendar")


def build_data(action: str, year: int, month: int, day: int):
    return f"simple_calendar&{action}&{year}&{month}&{day}"


def process_data(data: str) -> dict:
    data = data.split("&")[1:]
    return {"act": data[0], "year": data[1], "month": data[2], "day": data[3]}


class SimpleCalendar:
    # locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    local_month = {
        "January": "Январь",
        "February": "Февраль",
        "March": "Март",
        "April": "Апрель",
        "May": "Май",
        "June": "Июнь",
        "July": "Июль",
        "August": "Август",
        "September": "Сентябрь",
        "October": "Октябрь",
        "November": "Ноябрь",
        "December": "Декабрь",
    }

    async def start_calendar(
        self, year: int = datetime.now().year, month: int = datetime.now().month
    ) -> InlineKeyboardMarkup:
        """
        Creates an inline keyboard with the provided year and month
        :param int year: Year to use in the calendar, if None the current year is used.
        :param int month: Month to use in the calendar, if None the current month is used.
        :return: Returns InlineKeyboardMarkup object with the calendar.
        """
        inline_kb = []  # InlineKeyboardMarkup(row_width=7)
        ignore_callback = build_data("IGNORE", year, month, 0)  # for buttons with no answer
        # First row - Month and Year
        inline_row = []
        inline_row.append(
            InlineKeyboardButton(text=f"{year - 1}  <<", callback_data=build_data("PREV-YEAR", year, month, 1))
        )
        inline_row.append(
            InlineKeyboardButton(
                text=f"{self.local_month[calendar.month_name[month]]} {str(year)}", callback_data=ignore_callback
            )
        )
        inline_row.append(
            InlineKeyboardButton(text=f">>  {year + 1}", callback_data=build_data("NEXT-YEAR", year, month, 1))
        )
        inline_kb.append(inline_row)

        # Last row - Buttons
        inline_row = []
        inline_row.append(InlineKeyboardButton(text="<", callback_data=build_data("PREV-MONTH", year, month, 1)))
        if (year, month) != (datetime.now().year, datetime.now().month):
            inline_row.append(
                InlineKeyboardButton(text="Текущий месяц", callback_data=build_data("THIS_MONTH", year, month, 1))
            )
        else:
            inline_row.append(InlineKeyboardButton(text="месяц", callback_data=ignore_callback))

        inline_row.append(InlineKeyboardButton(text=">", callback_data=build_data("NEXT-MONTH", year, month, 1)))
        inline_kb.append(inline_row)

        # Second row - Week Days
        inline_row = []
        for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
            inline_row.append(InlineKeyboardButton(text=day, callback_data=ignore_callback))
        inline_kb.append(inline_row)

        # Calendar rows - Days of month

        month_calendar = calendar.monthcalendar(year, month)
        for week in month_calendar:
            inline_row = []
            for day in week:
                if day == 0:
                    inline_row.append(InlineKeyboardButton(text=" ", callback_data=ignore_callback))
                    continue

                if date.today().month == month and date.today().day == day and date.today().year == year:
                    text = f">{day}<"
                else:
                    text = str(day)
                inline_row.append(InlineKeyboardButton(text=text, callback_data=build_data("DAY", year, month, day)))
            inline_kb.append(inline_row)

        return InlineKeyboardMarkup(row_width=7, inline_keyboard=inline_kb)

    async def process_selection(self, query: CallbackQuery) -> tuple:
        """
        Process the callback_query. This method generates a new calendar if forward or
        backward is pressed. This method should be called inside a CallbackQueryHandler.
        :param query: callback_query, as provided by the CallbackQueryHandler
        :param data: callback_data, dictionary, set by calendar_callback
        :return: Returns a tuple (Boolean,datetime), indicating if a date is selected
                    and returning the date if so.
        """
        return_data = (False, None)
        # print(query.data)
        data = process_data(query.data)
        temp_date = datetime(int(data["year"]), int(data["month"]), 1)
        # processing empty buttons, answering with no action
        if data["act"] == "IGNORE":
            await query.answer(cache_time=60)
        # user picked a day button, return date
        if data["act"] == "DAY":
            await query.message.delete()  # removing inline keyboard
            return_data = True, date(int(data["year"]), int(data["month"]), int(data["day"]))
        # user navigates to previous year, editing message with new calendar
        if data["act"] == "PREV-YEAR":
            prev_date = datetime(int(data["year"]) - 1, int(data["month"]), 1)
            await query.message.edit_reply_markup(
                reply_markup=await self.start_calendar(int(prev_date.year), int(prev_date.month))
            )
        # user navigates to next year, editing message with new calendar
        if data["act"] == "NEXT-YEAR":
            next_date = datetime(int(data["year"]) + 1, int(data["month"]), 1)
            await query.message.edit_reply_markup(
                reply_markup=await self.start_calendar(int(next_date.year), int(next_date.month))
            )
        # user navigates to previous month, editing message with new calendar
        if data["act"] == "PREV-MONTH":
            prev_date = temp_date - timedelta(days=1)
            await query.message.edit_reply_markup(
                reply_markup=await self.start_calendar(int(prev_date.year), int(prev_date.month))
            )
        # user navigates to next month, editing message with new calendar
        if data["act"] == "NEXT-MONTH":
            next_date = temp_date + timedelta(days=31)
            await query.message.edit_reply_markup(
                reply_markup=await self.start_calendar(int(next_date.year), int(next_date.month))
            )

        if data["act"] == "THIS_MONTH":
            await query.message.edit_reply_markup(reply_markup=await self.start_calendar())
        # at some point user clicks DAY button, returning date
        return return_data
