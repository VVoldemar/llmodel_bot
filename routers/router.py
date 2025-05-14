import aiogram
import aiogram.fsm.context

import keyboards
import strings
import models.user

# import models.user

from aiogram import Router
from aiogram import filters
from aiogram import types
from . import keyboard

router = Router()


@router.message(filters.CommandStart())
async def start(message: types.Message):
    await message.answer(
        strings.GREETING,
        reply_markup=keyboards.reply.get_menu_keyboard()
    )


@router.message(aiogram.F.text.in_([
    strings.MENU_KEYBOARD.PROFILE,
    strings.MENU_KEYBOARD.MODEL,
    strings.MENU_KEYBOARD.HELP,
    strings.MENU_KEYBOARD.REFERRAL,
    strings.MENU_KEYBOARD.SETTINGS
]))
async def menu_handler(message: types.Message, state: aiogram.fsm.context.FSMContext,
                       user: models.user.User):  # user is injected by middleware
    match message.text:
        case strings.MENU_KEYBOARD.PROFILE:
            await message.answer(strings.profile_info(user), parse_mode="Markdown")
        case strings.MENU_KEYBOARD.MODEL:
            kb = await keyboards.inline.get_model_keyboard(user)
            await message.answer("Change model kb", reply_markup=kb)
        case strings.MENU_KEYBOARD.HELP:
            await message.answer("Support")
        case strings.MENU_KEYBOARD.REFERRAL:
            await message.answer("Referral")
        case strings.MENU_KEYBOARD.SETTINGS:
            await keyboard.set_initial_settings_state(state)
            initial_menu_key = keyboards.inline.MENU_MAIN
            kb = await keyboards.inline.get_settings_keyboard(initial_menu_key, user=user)
            message_text = keyboards.inline.MENU_TITLES.get(initial_menu_key, "Settings")
            sent_message = await message.answer(message_text, reply_markup=kb, parse_mode="Markdown")
            await state.update_data(prompt_message_id=sent_message.message_id)


@router.message(aiogram.filters.StateFilter(None), aiogram.F.text)
async def other_text_handler(message: types.Message):
    # TODO: AIchat
    await message.answer(f"Я получил: {message.text}. Используйте кнопки меню для взаимодействия.")
