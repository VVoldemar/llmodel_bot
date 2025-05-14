import aiogram
import aiogram.utils.keyboard
import sqlalchemy.orm as orm

import strings
import models.user

from . import callback_data

# import models.subscription


# Define menu keys
MENU_MAIN = "settings_main"
MENU_INSTRUCTION = strings.SETTINGS_MENUS.MENU_MAIN.CALLBACK_INSTRUCTION
MENU_CONTEXT = strings.SETTINGS_MENUS.MENU_MAIN.CALLBACK_CONTEXT
MENU_LANGUAGE = strings.SETTINGS_MENUS.MENU_MAIN.CALLBACK_LANGUAGE
MENU_SET_INSTRUCTION = strings.SETTINGS_MENUS.MENU_INSTRUCTION.CALLBACK_MENU_SET_INSTRUCTION

# Define action keys
ACTION_BACK = strings.SETTINGS_MENUS.ACTION_BACK

back_button = (strings.SETTINGS_MENUS.BACK, ACTION_BACK)

GENERAL_NAV_ACTIONS = {
    ACTION_BACK,
    MENU_INSTRUCTION,
    MENU_CONTEXT,
    MENU_LANGUAGE,
    strings.SETTINGS_MENUS.MENU_INSTRUCTION.CALLBACK_CHANGE_MODE,
    strings.SETTINGS_MENUS.MENU_CONTEXT.CALLBACK_CONTEXT_ON,
    strings.SETTINGS_MENUS.MENU_CONTEXT.CALLBACK_CONTEXT_OFF,
    strings.SETTINGS_MENUS.MENU_LANGUAGE.CALLBACK_ENGLISH,
    strings.SETTINGS_MENUS.MENU_LANGUAGE.CALLBACK_RUSSIAN,
}


def get_settings_menus(user: models.user.User):
    """Generates the menu structure dynamically based on user state."""
    return {
        MENU_MAIN: [
            (strings.SETTINGS_MENUS.MENU_MAIN.INSTRUCTION, MENU_INSTRUCTION),
            (strings.SETTINGS_MENUS.MENU_MAIN.CONTEXT, MENU_CONTEXT),
            (strings.SETTINGS_MENUS.MENU_MAIN.LANGUAGE, MENU_LANGUAGE),
        ],
        MENU_INSTRUCTION: [
            (strings.SETTINGS_MENUS.MENU_INSTRUCTION.EDIT, strings.SETTINGS_MENUS.MENU_INSTRUCTION.CALLBACK_EDIT),
            (
                strings.SETTINGS_MENUS.MENU_INSTRUCTION.MODE_ON
                if user.instruction_mode_on
                else strings.SETTINGS_MENUS.MENU_INSTRUCTION.MODE_OFF,
                strings.SETTINGS_MENUS.MENU_INSTRUCTION.CALLBACK_CHANGE_MODE
            ),
            back_button
        ],
        MENU_CONTEXT: [
            (
                strings.SETTINGS_MENUS.MENU_CONTEXT.CONTEXT_SELECTED * user.context_mode_on + strings.SETTINGS_MENUS.MENU_CONTEXT.CONTEXT_ON,
                strings.SETTINGS_MENUS.MENU_CONTEXT.CALLBACK_CONTEXT_ON
            ),
            (
                strings.SETTINGS_MENUS.MENU_CONTEXT.CONTEXT_SELECTED * (
                    not user.context_mode_on) + strings.SETTINGS_MENUS.MENU_CONTEXT.CONTEXT_OFF,
                strings.SETTINGS_MENUS.MENU_CONTEXT.CALLBACK_CONTEXT_OFF
            ),
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


MENU_TITLES = {
    MENU_MAIN: strings.SETTINGS_MENUS.DESCRIPTION.MENU_MAIN,
    MENU_INSTRUCTION: strings.SETTINGS_MENUS.DESCRIPTION.MENU_INSTRUCTION,
    MENU_CONTEXT: strings.SETTINGS_MENUS.DESCRIPTION.MENU_CONTEXT,
    MENU_LANGUAGE: strings.SETTINGS_MENUS.DESCRIPTION.MENU_LANGUAGE,
    MENU_SET_INSTRUCTION: strings.SETTINGS_MENUS.DESCRIPTION.MENU_SET_INSTRUCTION,
}


async def get_settings_keyboard(current_menu_key: str, user: models.user.User,) -> aiogram.types.InlineKeyboardMarkup:
    """Returns button markup for the specified settings menu.

    :param current_menu_key: The key of the current menu to display
    :param user: user object
    :returns: InlineKeyboardMarkup
    """
    builder = aiogram.utils.keyboard.InlineKeyboardBuilder()
    all_menus = get_settings_menus(user)
    menu_items = all_menus.get(current_menu_key, [])

    for text, action_key in menu_items:
        builder.button(text=text, callback_data=callback_data.SettingsCallback(action=action_key))

    builder.adjust(1)
    return builder.as_markup()



async def get_model_keyboard(user: models.user.User) -> aiogram.types.InlineKeyboardMarkup:
    """Returns button markup for the model selection."""
    builder = aiogram.utils.keyboard.InlineKeyboardBuilder()
    models = strings.MODELS.copy()

    if user.selected_model is not None and user.selected_model in models:
        models[user.selected_model] = models[user.selected_model] + strings.MODEL_SELECTED

    for model_id, model_name in models.items():
        builder.button(text=model_name, callback_data=callback_data.ModelCallback(model=model_id))

    builder.adjust(2)
    return builder.as_markup()