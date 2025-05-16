import os
import json
import asyncio

import aiogram
import aiogram.fsm.context
import aiogram.utils.formatting
import aiogram.utils.markdown
import aiohttp
import sqlalchemy.orm
from aiogram.exceptions import TelegramBadRequest

import keyboards
import strings
import models.user
import services.message_service

# import models.user

from aiogram import Router
from aiogram import filters
from aiogram import types
from . import keyboard

router = Router()

MAX_MESSAGE_LEN = 4096
# Buffer to avoid hitting the exact limit
SAFE_MAX_LEN = 4000
MIN_UPDATE_INTERVAL_SEC = 0.7  # Min interval between message edits to avoid "Too Many Requests"
THINK_TAG_START = {"<think>", "<reasoning>"}
THINK_TAG_END = {"</think>", "</reasoning>"}


async def _update_message_helper(bot: aiogram.Bot, message_to_edit: types.Message, new_text: str,
                                 new_markup: types.InlineKeyboardMarkup | None = None):
    """Helper to edit a message, similar to _update_message."""
    if not message_to_edit:
        return None
    if message_to_edit.text == new_text and message_to_edit.reply_markup == new_markup:
        return message_to_edit
    try:
        return await bot.edit_message_text(
            text=new_text,
            chat_id=message_to_edit.chat.id,
            message_id=message_to_edit.message_id,
            reply_markup=new_markup,
            parse_mode="HTML"
        )
    except aiogram.exceptions.TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return message_to_edit
        raise


async def send_or_update_formatted_message(bot: aiogram.Bot, chat_id: int, text_content: str,
                                           current_message_obj: types.Message | None,
                                           is_think_block_content: bool,
                                           is_last_update: bool = False) -> types.Message | None:
    """
    Formats text (e.g., as expandable blockquote if needed) and sends/updates.
    Returns the sent/updated message object or None if sending failed.
    """
    if not text_content.strip() and not (current_message_obj and current_message_obj.text == "⏳"):
        if current_message_obj:
            return current_message_obj
        return None

    final_text_to_send = aiogram.utils.formatting.Text("")
    if is_think_block_content:
        final_text_to_send = aiogram.utils.formatting.Text(text_content)
        stripped_content = text_content.strip()
        if stripped_content:
            stripped_content = aiogram.utils.formatting.Text(stripped_content)
            final_text_to_send = f"<blockquote{" expandable" if is_last_update else ""}>\n" + stripped_content.as_html() + "</blockquote>"

    else:
        final_text_to_send = aiogram.utils.formatting.Text(text_content).as_html()

    if not final_text_to_send and not (current_message_obj and current_message_obj.text == "⏳"):
        if current_message_obj:
            return current_message_obj
        return None

    new_message_sent = False
    if current_message_obj:
        try:
            updated_msg = await _update_message_helper(bot=bot, message_to_edit=current_message_obj,
                                                       new_text=final_text_to_send, new_markup=None)
            return updated_msg
        except TelegramBadRequest as e:
            if "message to edit not found" in str(e).lower() or \
                    "message can't be edited" in str(e).lower():
                print(f"Cannot edit message {current_message_obj.message_id}, sending new. Error: {e}")
                new_message_sent = True
            elif "message is not modified" not in str(e).lower():
                print(
                    f"Telegram API error on update: {e}. Formatted Text: '{final_text_to_send[:100]}...'")
                new_message_sent = True
            else:
                return current_message_obj
    else:
        new_message_sent = True

    if new_message_sent:
        try:
            parse_mode = "MarkdownV2" if not is_think_block_content else "HTML"
            return await bot.send_message(chat_id, final_text_to_send, parse_mode="HTML")
        except TelegramBadRequest as e:
            print(f"Telegram API error on send: {e}. Formatted Text: '{final_text_to_send[:100]}...'")
            # escaped_text = hide_link(text_content) # Use original raw content for hide_link
            # try:
            # print(f"Attempting to send with hide_link: {escaped_text[:100]}...")
            # return await bot.send_message(chat_id, escaped_text, parse_mode=None)
            # except Exception as e:
            #     pass
    return None


@router.message(filters.CommandStart())
async def start(message: types.Message, session: sqlalchemy.orm.Session, user: models.user.User):
    await message.answer(
        strings.GREETING,
        reply_markup=keyboards.reply.get_menu_keyboard()
    )
    try:
        services.message_service.delete_messages(session, user)
    except Exception:
        pass


@router.message(aiogram.filters.command.Command("clear_context"))
@router.message(aiogram.filters.command.Command("clearcontext"))
@router.message(aiogram.filters.command.Command("clear"))
async def clear_context(message: aiogram.types.Message, session: sqlalchemy.orm.Session, user: models.user.User):
    try:
        services.message_service.delete_messages(session, user)
        await message.answer(strings.CLEAR_CONTEXT.SUCESS)
    except Exception:
        await message.answer(strings.CLEAR_CONTEXT.ERROR)


@router.message(aiogram.F.text.in_([
    strings.MENU_KEYBOARD.PROFILE,
    strings.MENU_KEYBOARD.MODEL,
    strings.MENU_KEYBOARD.HELP,
    strings.MENU_KEYBOARD.REFERRAL,
    strings.MENU_KEYBOARD.SETTINGS
]))
async def menu_handler(message: types.Message, state: aiogram.fsm.context.FSMContext,
                       user: models.user.User):
    match message.text:
        case strings.MENU_KEYBOARD.PROFILE:
            await message.answer(strings.profile_info(user), parse_mode="Markdown")
        case strings.MENU_KEYBOARD.MODEL:
            kb = await keyboards.inline.get_model_keyboard(user)
            await message.answer("Change model kb", reply_markup=kb)
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
@router.message(keyboard.MenuState.navigating, aiogram.F.text)
async def other_text_handler(message: types.Message, user: models.user.User, session: sqlalchemy.orm.Session,
                             bot: aiogram.Bot):
    active_message_object: types.Message | None = None
    try:
        active_message_object = await message.answer("⏳", parse_mode="MarkdownV2")
    except TelegramBadRequest:
        await message.answer("Error: Could not start AI response.")  # TODO: Localize
        return

    current_text_segment = ""
    is_in_think_block = False
    last_update_ts = asyncio.get_event_loop().time()

    # --- AI Request Setup ---
    # ai_model = "ministral-3b"
    ai_model = user.selected_model or "ministral-3b"
    api_key = os.getenv("AI_API_KEY", "dac877e7-4afd-4aa4-9c6f-97eedea5810c")
    stream_url = os.getenv("AI_STREAM_URL", "http://127.0.0.1:5050/stream/")

    ai_messages = []
    if user.instruction_mode_on and user.instruction:
        ai_messages.append({"role": "system", "content": user.instruction})
    ai_messages += services.message_service.get_context_messages(session, user)

    # TODO: Add context messages if user.context_mode_on is True

    ai_messages.append({"role": "user", "content": message.text})
    request_data = {
        "model": ai_model,
        "messages": ai_messages,
        "api_key": api_key
    }
    json_request_data = json.dumps(request_data)
    headers = {
        "Content-Type": "application/json"
    }
    # --- End AI Request Setup ---

    processing_buffer = ""  # Accumulates raw text from stream
    current_text_segment = ""  # Accumulates raw text for the current logical block (normal or think)
    is_in_think_block = False
    last_update_ts = asyncio.get_event_loop().time()
    full_response_for_history = ""

    try:
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(stream_url, data=json_request_data, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"AI API Error {response.status}: {error_text[:500]}")
                    active_message_object = await send_or_update_formatted_message(bot, message.chat.id,
                                                                                   f"AI Error: {response.status}",
                                                                                   active_message_object, False)
                    return

                async for chunk_bytes in response.content.iter_any():
                    if not chunk_bytes:
                        continue
                    print(chunk_bytes.decode("utf-8", errors="ignore"))

                    processing_buffer += chunk_bytes.decode("utf-8", errors="ignore")
                    full_response_for_history += processing_buffer

                    while True:
                        chunk_to_process_further = ""

                        if is_in_think_block:
                            for tag_end in THINK_TAG_END:
                                end_tag_pos = processing_buffer.find(tag_end)
                                if end_tag_pos != -1:
                                    found_tag = tag_end
                                    break
                            if end_tag_pos != -1:
                                segment = processing_buffer[:end_tag_pos]
                                current_text_segment += segment
                                processing_buffer = processing_buffer[end_tag_pos + len(found_tag):]

                                if current_text_segment.strip():
                                    active_message_object = await send_or_update_formatted_message(
                                        bot, message.chat.id, current_text_segment, active_message_object, True,
                                        is_last_update=True
                                    )

                                # active_message_object = await send_or_update_formatted_message(
                                #     bot, message.chat.id, current_text_segment, active_message_object,
                                #     is_in_think_block,
                                #     is_last_update=True
                                # )
                                is_in_think_block = False
                                current_text_segment = ""
                                active_message_object = None
                            else:
                                current_text_segment += processing_buffer
                                processing_buffer = ""
                                break
                        else:
                            for tag_start in THINK_TAG_START:
                                start_tag_pos = processing_buffer.find(tag_start)
                                if start_tag_pos != -1:
                                    found_tag = tag_start
                                    break

                            if start_tag_pos != -1:
                                segment = processing_buffer[:start_tag_pos]
                                current_text_segment += segment
                                processing_buffer = processing_buffer[start_tag_pos + len(found_tag):]

                                if current_text_segment.strip():
                                    active_message_object = await send_or_update_formatted_message(
                                        bot, message.chat.id, current_text_segment, active_message_object, False
                                    )

                                is_in_think_block = True
                                current_text_segment = ""
                            else:
                                current_text_segment += processing_buffer
                                processing_buffer = ""
                                break

                        if not processing_buffer:
                            break

                    now = asyncio.get_event_loop().time()
                    if len(current_text_segment) > SAFE_MAX_LEN or \
                            (
                                    current_text_segment.strip() and now - last_update_ts > MIN_UPDATE_INTERVAL_SEC and active_message_object is not None):

                        text_to_format_and_send = current_text_segment
                        temp_remaining_text = ""

                        is_last_current_message_update = False
                        if len(current_text_segment) > SAFE_MAX_LEN:
                            split_at = SAFE_MAX_LEN

                            text_to_format_and_send = current_text_segment[:split_at]
                            temp_remaining_text = current_text_segment[split_at:]
                            is_last_current_message_update = True


                        if text_to_format_and_send.strip() or (
                                active_message_object and active_message_object.text == "⏳"):
                            active_message_object = await send_or_update_formatted_message(
                                bot, message.chat.id, text_to_format_and_send, active_message_object, is_in_think_block,
                                is_last_update=is_last_current_message_update)

                        if temp_remaining_text.strip():
                            current_text_segment = temp_remaining_text
                        if temp_remaining_text.strip():
                            if active_message_object and text_to_format_and_send.strip():
                                print("here")
                                active_message_object = None
                        last_update_ts = now

                if processing_buffer:
                    current_text_segment += processing_buffer
                    processing_buffer = ""

                if current_text_segment.strip():
                    active_message_object = await send_or_update_formatted_message(
                        bot=bot, chat_id=message.chat.id, text_content=current_text_segment,
                        current_message_obj=active_message_object, is_think_block_content=is_in_think_block
                    )

    except aiohttp.ClientError as e:
        err_msg = "Error: Could not connect to AI service."  # TODO: Localize
        if active_message_object:
            await send_or_update_formatted_message(bot, message.chat.id, err_msg, active_message_object, False)
        else:
            await message.answer(err_msg)
    except TelegramBadRequest as e:
        await message.answer("Error: A problem occurred while displaying the AI response.")  # TODO: Localize
    except Exception as e:
        err_msg = "Error: An unexpected error occurred."  # TODO: Localize
        if active_message_object:
            await send_or_update_formatted_message(bot=bot, chat_id=message.chat.id, text_content=err_msg,
                                                   current_message_obj=active_message_object,
                                                   is_think_block_content=False)
        else:
            await message.answer(err_msg)
        raise e

    services.message_service.add_message(session, message.text, user)
    if full_response_for_history:
        services.message_service.add_message(session, full_response_for_history, user, is_from_user=False)
