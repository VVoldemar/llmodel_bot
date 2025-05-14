import aiogram
import aiogram.filters
import aiogram.fsm.state
import aiogram.fsm.context
import keyboards
import sqlalchemy.orm as orm

from aiogram import Router
from aiogram import filters
from aiogram import types

import models.user
import strings
import services.user_service

kb_router = Router()


class MenuState(aiogram.fsm.state.StatesGroup):
    navigating = aiogram.fsm.state.State()
    waiting_for_instructions = aiogram.fsm.state.State()

async def set_initial_settings_state(state: aiogram.fsm.context.FSMContext):
    await state.set_state(MenuState.navigating)
    # Initialize history with the key of the main settings menu
    await state.update_data(history=[keyboards.inline.MENU_MAIN]) 


@kb_router.callback_query(MenuState.navigating, keyboards.callback_data.SettingsCallback.filter())
async def navigate_settings(query: types.CallbackQuery, callback_data: keyboards.callback_data.SettingsCallback, state: aiogram.fsm.context.FSMContext, user: models.user.User):
    await query.answer()

    action = callback_data.action
    fsm_data = await state.get_data()
    history = fsm_data.get("history", [keyboards.inline.MENU_MAIN])

    current_menu_key = history[-1]
    next_menu_key = None
    additinal_info = ""

    if action == keyboards.inline.ACTION_BACK:
        if len(history) > 1:
            history.pop()
        next_menu_key = history[-1]
    elif action in keyboards.inline.SETTINGS_MENUS:
        if action != current_menu_key:
             history.append(action)
        next_menu_key = action
    else:
        match action:
            case strings.SETTINGS_MENUS.MENU_INSTRUCTION.CALLBACK_EDIT:
                # set state
                await state.set_state(MenuState.waiting_for_instructions)
        await query.message.answer(f"Action: {action} executed (implementation pending).")
        next_menu_key = current_menu_key # Stay on the current menu after a leaf action

    if action == keyboards.inline.MENU_INSTRUCTION:
        if user.instruction is not None:
            additinal_info = user.instruction
        else:
            additinal_info = strings.SETTINGS_MENUS.MENU_INSTRUCTION.INSTRUCTION_NOT_ASSIGNED

    if next_menu_key:
        await state.update_data(history=history)
        kb = await keyboards.inline.get_settings_keyboard(next_menu_key)
        message_text = keyboards.inline.MENU_TITLES.get(next_menu_key, "Settings") + additinal_info
        
        # Only edit if the content or markup has changed
        if query.message.text != message_text or query.message.reply_markup != kb:
            await query.message.edit_text(message_text, reply_markup=kb, parse_mode="Markdown")


@kb_router.message(aiogram.filters.StateFilter(MenuState.waiting_for_instructions))
async def set_instructions(message: aiogram.types.Message, session: orm.Session, state: aiogram.fsm.context.FSMContext, user: models.user.User):
    await services.user_service.set_instruction(message.text, session, user)
    await state.set_state(MenuState.navigating)
    fsm_data = await state.get_data()
    key = fsm_data.get("history", [keyboards.inline.MENU_MAIN])[-1]
    previous_kb = await keyboards.inline.get_settings_keyboard(key)
    message_text = strings.SETTINGS_MENUS.MENU_INSTRUCTION.INSTRUCTION_UPDATED + '_' + message.text # TODO: display new role as a citation
    await message.answer(message_text, reply_markup=previous_kb, parse_mode="MarkdownV2")