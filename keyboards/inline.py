import aiogram
import aiogram.utils.keyboard
import sqlalchemy.orm as orm

import strings

from . import callback_data
# import models.subscription


# Define menu keys
MENU_MAIN = "settings_main"
MENU_INSTRUCTION = strings.SETTINGS_MENUS.MENU_MAIN.CALLBACK_INSTRUCTION
MENU_CONTEXT = strings.SETTINGS_MENUS.MENU_MAIN.CALLBACK_CONTEXT
MENU_LANGUAGE = strings.SETTINGS_MENUS.MENU_MAIN.CALLBACK_LANGUAGE
MENU_SET_INSTRUCTION = strings.SETTINGS_MENUS.MENU_INSTRUCTION.CALLBACK_EDIT

# Define action keys
ACTION_BACK = strings.SETTINGS_MENUS.ACTION_BACK
# Add other specific action keys if needed, e.g., ACTION_VIEW_INSTRUCTION = "view_instruction"

back_button = (strings.SETTINGS_MENUS.BACK, ACTION_BACK)

SETTINGS_MENUS = {
    MENU_MAIN: [
        (strings.SETTINGS_MENUS.MENU_MAIN.INSTRUCTION, MENU_INSTRUCTION),
        (strings.SETTINGS_MENUS.MENU_MAIN.CONTEXT, MENU_CONTEXT),
        (strings.SETTINGS_MENUS.MENU_MAIN.LANGUAGE, MENU_LANGUAGE),
    ],
    MENU_INSTRUCTION: [
        (strings.SETTINGS_MENUS.MENU_INSTRUCTION.EDIT, strings.SETTINGS_MENUS.MENU_INSTRUCTION.CALLBACK_EDIT), 
        (strings.SETTINGS_MENUS.MENU_INSTRUCTION.CHANGE_MODE, strings.SETTINGS_MENUS.MENU_INSTRUCTION.CALLBACK_CHANGE_MODE),
        back_button
    ],
    MENU_CONTEXT: [
        (strings.SETTINGS_MENUS.MENU_CONTEXT.CONTEXT_ON, strings.SETTINGS_MENUS.MENU_CONTEXT.CALLBACK_CONTEXT_ON),
        (strings.SETTINGS_MENUS.MENU_CONTEXT.CONTEXT_OFF, strings.SETTINGS_MENUS.MENU_CONTEXT.CALLBACK_CONTEXT_OFF),
        back_button
    ],
    MENU_LANGUAGE: [
        (strings.SETTINGS_MENUS.MENU_LANGUAGE.ENGLISH, strings.SETTINGS_MENUS.MENU_LANGUAGE.CALLBACK_ENGLISH),
        (strings.SETTINGS_MENUS.MENU_LANGUAGE.RUSSIAN, strings.SETTINGS_MENUS.MENU_LANGUAGE.CALLBACK_RUSSIAN),
        back_button
    ],
    MENU_SET_INSTRUCTION: [
        back_button
    ]
}

# Titles for menus (optional, for message text)
MENU_TITLES = {
    MENU_MAIN: strings.SETTINGS_MENUS.DESCRIPTION.MENU_MAIN,
    MENU_INSTRUCTION: strings.SETTINGS_MENUS.DESCRIPTION.MENU_INSTRUCTION,
    MENU_CONTEXT: strings.SETTINGS_MENUS.DESCRIPTION.MENU_CONTEXT,
    MENU_LANGUAGE: strings.SETTINGS_MENUS.DESCRIPTION.MENU_LANGUAGE,
}

async def get_settings_keyboard(current_menu_key: str, prefix: str="", prefix_apply_index=-1) -> aiogram.types.InlineKeyboardMarkup:
    """Returns button markup for the specified settings menu.

    :param current_menu_key: The key of the current menu to display
    :param user: user object
    :param prefix: The string that will be added to beginning of button text with `prefix_apply_index` number
    :param prefix_apply_index: The number off button, to which `prefix` will be applied
    :returns: InlineKeyboardMarkup
    """
    builder = aiogram.utils.keyboard.InlineKeyboardBuilder()
    menu_items = SETTINGS_MENUS.get(current_menu_key, [])

    for i, (text, action_key) in enumerate(menu_items):
        if i == prefix_apply_index:
            text = prefix + text
        builder.button(text=text, callback_data=callback_data.SettingsCallback(action=action_key))
    
    # Adjust button layout as needed, e.g., 1 button per row or 2 then 1 for back
    builder.adjust(1) 
    return builder.as_markup()