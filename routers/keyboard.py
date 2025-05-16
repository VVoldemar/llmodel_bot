import logging
import aiogram
import aiogram.filters
import aiogram.exceptions
import aiogram.fsm.state
import aiogram.fsm.context
import sqlalchemy.orm as orm

from aiogram import Router
from aiogram import filters
from aiogram import types

import keyboards
import models.user
import strings
import services.user_service

kb_router = Router()


class MenuState(aiogram.fsm.state.StatesGroup):
    navigating = aiogram.fsm.state.State()
    waiting_for_instructions = aiogram.fsm.state.State()


async def set_initial_settings_state(state: aiogram.fsm.context.FSMContext):
    await state.set_state(MenuState.navigating)
    await state.update_data(history=[keyboards.inline.MENU_MAIN], prompt_message_id=None)


async def _update_message(message: aiogram.types.Message, new_text: str,
                          new_markup: aiogram.types.InlineKeyboardMarkup | None, bot: aiogram.Bot):
    """Helper function to edit message text and markup, handling 'message is not modified' error."""
    if message.text != new_text or message.reply_markup != new_markup:
        try:
            await bot.edit_message_text(text=new_text, chat_id=message.chat.id, message_id=message.message_id,
                                        reply_markup=new_markup, parse_mode="MarkdownV2")
        except aiogram.exceptions.TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                logging.info("Message not modified, skipping edit.")
            else:
                logging.error(f"Error editing message: {e}")


@kb_router.callback_query(MenuState.navigating, )
@kb_router.callback_query(MenuState.navigating, keyboards.callback_data.SettingsCallback.filter())
async def navigate_settings(query: types.CallbackQuery, callback_data: keyboards.callback_data.SettingsCallback,
                            state: aiogram.fsm.context.FSMContext, user: models.user.User, session: orm.Session,
                            bot: aiogram.Bot):
    await query.answer()

    action = callback_data.action
    fsm_data = await state.get_data()
    history = fsm_data.get("history", [keyboards.inline.MENU_MAIN])

    current_menu_key = history[-1]
    next_menu_key = current_menu_key
    additinal_info = ""

    dynamic_menus = keyboards.inline.get_settings_menus(user)

    if action == keyboards.inline.ACTION_BACK:
        if len(history) > 1:
            history.pop()
        next_menu_key = history[-1]
    elif action in dynamic_menus:
        if action != current_menu_key:
            history.append(action)
        next_menu_key = action
    else:
        match action:
            case strings.SETTINGS_MENUS.MENU_INSTRUCTION.CALLBACK_CHANGE_MODE:
                user.instruction_mode_on = not user.instruction_mode_on
            case strings.SETTINGS_MENUS.MENU_CONTEXT.CALLBACK_CONTEXT_ON:
                user.context_mode_on = True
            case strings.SETTINGS_MENUS.MENU_CONTEXT.CALLBACK_CONTEXT_OFF:
                user.context_mode_on = False
            case strings.SETTINGS_MENUS.MENU_INSTRUCTION.CALLBACK_EDIT:
                if history[-1] != keyboards.inline.MENU_SET_INSTRUCTION:
                    history.append(keyboards.inline.MENU_SET_INSTRUCTION)
                next_menu_key = history[-1]
                await state.update_data(prompt_message_id=query.message.message_id, history=history)
                await state.set_state(MenuState.waiting_for_instructions)
        session.add(user)
        session.flush()

    if action == keyboards.inline.MENU_INSTRUCTION:
        if user.instruction is not None:
            additinal_info = f"\n```{user.instruction}```"
        else:
            additinal_info = strings.SETTINGS_MENUS.MENU_INSTRUCTION.INSTRUCTION_NOT_ASSIGNED

    kb = await keyboards.inline.get_settings_keyboard(next_menu_key, user)
    new_text = query.message.md_text if next_menu_key not in keyboards.inline.MENU_TITLES else keyboards.inline.MENU_TITLES.get(
        next_menu_key)
    new_text += additinal_info
    await _update_message(query.message, new_text, kb, bot)


@kb_router.message(MenuState.waiting_for_instructions)
async def set_instructions(message: aiogram.types.Message, session: orm.Session, state: aiogram.fsm.context.FSMContext,
                           user: models.user.User, bot: aiogram.Bot):
    await services.user_service.set_instruction(message.text, session, user)

    fsm_data = await state.get_data()
    history = fsm_data.get("history", [])
    prompt_message_id_to_delete = fsm_data.get("prompt_message_id")

    if prompt_message_id_to_delete:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=prompt_message_id_to_delete)
        except Exception as e:
            logging.warning(f"Could not delete prompt message {prompt_message_id_to_delete}: {e}")

    if history and history[-1] == keyboards.inline.MENU_SET_INSTRUCTION:
        history.pop()

    current_menu_key = history[-1] if history else keyboards.inline.MENU_INSTRUCTION
    if not history:
        history.append(keyboards.inline.MENU_MAIN)
        current_menu_key = keyboards.inline.MENU_MAIN

    await state.set_state(MenuState.navigating)
    await state.update_data(history=history, prompt_message_id=None)

    kb = await keyboards.inline.get_settings_keyboard(current_menu_key, user=user)

    menu_display_text = keyboards.inline.MENU_TITLES.get(current_menu_key, "Settings")
    if current_menu_key == keyboards.inline.MENU_INSTRUCTION:
        menu_display_text = strings.SETTINGS_MENUS.MENU_INSTRUCTION.INSTRUCTION_UPDATED + f"```{user.instruction}```"

    new_menu_message = await bot.send_message(
        chat_id=message.chat.id,
        text=menu_display_text,
        reply_markup=kb,
        parse_mode="Markdown"
    )

    await state.update_data(prompt_message_id=new_menu_message.message_id)


@kb_router.callback_query(MenuState.waiting_for_instructions, keyboards.callback_data.SettingsCallback.filter())
async def navigate_settings_in_other_state(query: types.CallbackQuery,
                                           callback_data: keyboards.callback_data.SettingsCallback,
                                           state: aiogram.fsm.context.FSMContext, user: models.user.User,
                                           session: orm.Session, bot: aiogram.Bot):
    await navigate_settings(query, callback_data, state, user, session, bot)
    await state.set_state(MenuState.navigating)


@kb_router.callback_query(keyboards.callback_data.ModelCallback.filter())
async def change_model(query: aiogram.types.CallbackQuery,
                       callback_data: keyboards.callback_data.ModelCallback,
                       session: orm.Session,
                       user: models.user.User,
                       bot: aiogram.Bot):
    await query.answer()
    model = callback_data.model
    if model in strings.MODELS and user.selected_model != model:
        user.selected_model = model
        session.add(user)
        session.flush()

    kb = await keyboards.inline.get_model_keyboard(user)

    await _update_message(query.message, query.message.md_text, kb, bot)