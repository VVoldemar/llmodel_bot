import aiogram
import aiogram.types
import aiogram.utils.keyboard
import strings

from . import callback_data


def get_menu_keyboard() -> aiogram.utils.keyboard.ReplyKeyboardMarkup:
    """Returns menu keyboard. Some buttons show only if user is subscriber

    :return: ReplyKeyboardMarkup
    """
    builder = aiogram.utils.keyboard.ReplyKeyboardBuilder()

    builder.row(
        aiogram.types.KeyboardButton(text=strings.MENU_KEYBOARD.PROFILE),
        aiogram.types.KeyboardButton(text=strings.MENU_KEYBOARD.REFERRAL)
    )
    builder.row(
        aiogram.types.KeyboardButton(text=strings.MENU_KEYBOARD.MODEL)
    )
    builder.row(
        aiogram.types.KeyboardButton(text=strings.MENU_KEYBOARD.SETTINGS)
    )
    return builder.as_markup(resize_keyboard=True)