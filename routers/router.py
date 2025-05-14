import aiogram
import aiogram.fsm.context

import keyboards
import strings

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

@router.message()
async def message(message: types.Message, state: aiogram.fsm.context.FSMContext):
    match message.text:
        case strings.MENU_KEYBOARD.PROFILE:
            await message.answer("Profile")
        case strings.MENU_KEYBOARD.MODEL:
            await message.answer("Change model kb")
        case strings.MENU_KEYBOARD.HELP:
            await message.answer("Support")
        case strings.MENU_KEYBOARD.REFERRAL:
            await message.answer("Referral")
        case strings.MENU_KEYBOARD.SETTINGS:
            await keyboard.set_initial_settings_state(state) # Use the renamed function
            initial_menu_key = keyboards.inline.MENU_MAIN
            kb = await keyboards.inline.get_settings_keyboard(initial_menu_key)
            message_text = keyboards.inline.MENU_TITLES.get(initial_menu_key, "Settings")
            await message.answer(message_text, reply_markup=kb, parse_mode="Markdown")
        case _:
            await message.answer(message.text)