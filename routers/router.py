import os
import json
import asyncio
import logging

import aiogram
import aiogram.fsm.state
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

logging.basicConfig(level=logging.INFO)

router = Router()

MAX_MESSAGE_LEN = 4096
# Buffer to avoid hitting the exact limit
SAFE_MAX_LEN = 4000
MIN_UPDATE_INTERVAL_SEC = 1.1  # Min interval between message edits to avoid "Too Many Requests"
THINK_TAG_START = {"<think>", "<reasoning>"}
THINK_TAG_END = {"</think>", "</reasoning>"}

_recently_processed_media_groups = {}
_processing_lock = asyncio.Lock()

# Timeout for considering a media group
MEDIA_GROUP_PROCESS_TIMEOUT = 30


class LoadState(aiogram.fsm.state.StatesGroup):
    loading_profile_pic = aiogram.fsm.state.State()


def _get_escaped_text(text: str, is_think_block_content: bool):
    """Returns escaped html text if `is_think_block_content`, else md escaped text"""
    text_to_send = aiogram.utils.formatting.Text(text)
    if is_think_block_content:
        escaped_text = text_to_send.as_html()
    else:
        escaped_text = text_to_send.as_markdown()

    return escaped_text


async def _update_message_helper(bot: aiogram.Bot,
                                 message_to_edit: types.Message,
                                 new_text: str,
                                 new_markup: types.InlineKeyboardMarkup | None = None,
                                 parse_mode: str = "HTML"):
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
            parse_mode=parse_mode
        )
    except aiogram.exceptions.TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return message_to_edit
        raise


async def send_or_update_formatted_message(bot: aiogram.Bot,
                                           chat_id: int,
                                           text_content: str,
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

    escaped_text = _get_escaped_text(text_content, is_think_block_content)
    if is_think_block_content:
        final_text_to_send = f"<blockquote{" expandable" if is_last_update else ""}>\n" + escaped_text + "</blockquote>"

    else:
        final_text_to_send = text_content

    if not final_text_to_send and not (current_message_obj and current_message_obj.text == "⏳"):
        if current_message_obj:
            return current_message_obj
        return None

    parse_mode = "Markdown" if not is_think_block_content else "HTML"
    new_message_sent = False
    if current_message_obj:
        try:
            updated_msg = await _update_message_helper(bot=bot, message_to_edit=current_message_obj,
                                                       new_text=final_text_to_send, new_markup=None,
                                                       parse_mode=parse_mode)
            return updated_msg
        except TelegramBadRequest as e:
            if "message to edit not found" in str(e).lower() or \
                    "message can't be edited" in str(e).lower():
                logging.info(f"Cannot edit message {current_message_obj.message_id}, sending new. Error: {e}")
                new_message_sent = True
            elif "message is not modified" not in str(e).lower():
                logging.warning(  # Changed to warning and added more details
                    f"Telegram API error on update (message_id: {current_message_obj.message_id if current_message_obj else 'None'}): {e}. Error type: {type(e)}. Falling back to sending new message. Text: '{final_text_to_send[:100]}...'")
                new_message_sent = True
                # logging.info(
                #     f"Telegram API error on update: {e}. Formatted Text: '{final_text_to_send[:100]}...'")
                new_message_sent = True
            else:
                return current_message_obj
    else:
        new_message_sent = True

    if new_message_sent:
        try:
            return await bot.send_message(chat_id, final_text_to_send, parse_mode=parse_mode)
        except TelegramBadRequest as e:
            logging.info(f"Telegram API error on send: {e}. Formatted Text: '{final_text_to_send[:100]}...'")
            # escaped_text = hide_link(text_content) # Use original raw content for hide_link
            try:
                parse_mode = "MarkdownV2"
                final_text_to_send = _get_escaped_text(text_content, is_think_block_content, parse_mode=parse_mode)
                return await bot.send_message(chat_id, final_text_to_send, parse_mode=parse_mode)
            except Exception:
                logging.warning(f"Telegram API error on send: {e}. Formatted Text: '{final_text_to_send[:100]}...'")
        # logging.info(f"Attempting to send with hide_link: {escaped_text[:100]}...")




        # try:
        # return await bot.send_message(chat_id, escaped_text, parse_mode=None)
        # except Exception as e:
        #     pass
    return None


@router.message(filters.CommandStart())
async def start(message: types.Message,
                session: sqlalchemy.orm.Session,
                user: models.user.User,
                command: aiogram.filters.CommandObject):
    if command.args and command.args.isnumeric():
        referrer_id = int(command.args)
        if referrer_id != user.id and user.referrer_id is None:
            user.referrer_id = referrer_id

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
async def clear_context(message: aiogram.types.Message,
                        session: sqlalchemy.orm.Session,
                        user: models.user.User):
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
                       user: models.user.User, bot: aiogram.Bot):
    match message.text:
        case strings.MENU_KEYBOARD.PROFILE:
            file_name = f"profile_images/{user.id}.jpg"
            if os.path.isfile(file_name):
                photo = aiogram.types.FSInputFile(file_name)
                await message.answer_photo(photo)

            await message.answer(strings.profile_info(user), parse_mode="Markdown")

        case strings.MENU_KEYBOARD.MODEL:
            kb = await keyboards.inline.get_model_keyboard(user)
            await message.answer(strings.CHANGE_MODEL_TEXT, reply_markup=kb)

        case strings.MENU_KEYBOARD.REFERRAL:
            promo_text = await strings.promo(user, bot)
            await message.answer(promo_text)

        case strings.MENU_KEYBOARD.SETTINGS:
            await keyboard.set_initial_settings_state(state)
            initial_menu_key = keyboards.inline.MENU_MAIN

            kb = await keyboards.inline.get_settings_keyboard(initial_menu_key, user=user)
            message_text = keyboards.inline.MENU_TITLES.get(initial_menu_key, "Settings")
            sent_message = await message.answer(message_text, reply_markup=kb, parse_mode="Markdown")
            await state.update_data(prompt_message_id=sent_message.message_id)


@router.message(aiogram.filters.command.Command("profile_image"))
async def profile_image(message: aiogram.types.Message,
                        state: aiogram.fsm.context.FSMContext):
    await state.set_state(LoadState.loading_profile_pic)

    kb = await keyboards.inline.get_profile_picture_keyboard()
    await message.answer(strings.PROFILE_PHOTO.LOAD_PHOTO_TEXT, reply_markup=kb)


@router.message(LoadState.loading_profile_pic, aiogram.F.photo)
async def load_and_save_profile_image(message: aiogram.types.Message,
                                      user: models.user.User,
                                      session: sqlalchemy.orm.Session,
                                      state: aiogram.fsm.context.FSMContext,
                                      bot: aiogram.Bot):
    picture = message.photo[-1]
    file_name = f"profile_images/{user.id}.jpg"
    media_group_id = message.media_group_id

    process_this_image_db_update = True

    if media_group_id:
        async with _processing_lock:
            current_time = asyncio.get_event_loop().time()
            # Clean up old entries
            for key, ts in list(_recently_processed_media_groups.items()):
                if current_time - ts > MEDIA_GROUP_PROCESS_TIMEOUT:
                    del _recently_processed_media_groups[key]

            processing_key = (user.id, media_group_id)

            if processing_key in _recently_processed_media_groups:
                process_this_image_db_update = False
                logging.info(
                    f"Media group {media_group_id} for user {user.id} (image {message.photo[0].file_unique_id}): already processed or processing first image. Skipping DB update for profile_media_group_id.")
            else:
                # The first image of this media group
                _recently_processed_media_groups[processing_key] = current_time
                logging.info(
                    f"Processing first image of media group {media_group_id} for user {user.id} (image {message.photo[0].file_unique_id}).")
                if user.profile_media_group_id == media_group_id:
                    logging.info(
                        f"Media group {media_group_id} for user {user.id} already set in DB. Skipping DB update.")
                    process_this_image_db_update = False

    try:
        file = await bot.get_file(picture.file_id)
        file_path = file.file_path

        if process_this_image_db_update:
            os.makedirs(os.path.dirname(file_name), exist_ok=True)  # Na vsyakiy sluchay
            await bot.download_file(file_path, destination=file_name)
            logging.info(f"Downloaded photo {picture.file_id} to {file_name} for user {user.id}")

            user.profile_media_group_id = media_group_id
            session.add(user)

            await message.reply(strings.PROFILE_PHOTO.SAVE_PHOTO_SUCCESS)
            await state.clear()
    except sqlalchemy.exc.OperationalError as e:
        if "database is locked" in str(e).lower():
            logging.warning(
                f"Database locked for user {user.id} during profile image save: {e}. Session will be rolled back.")
            await message.reply("Failed to save profile picture due to a temporary database issue. Please try again.")
        else:
            logging.error(f"SQLAlchemy OperationalError for user {user.id}: {e}")
            await message.reply(strings.PROFILE_PHOTO.SAVE_PHOTO_FAILED)
    except Exception as e:
        logging.error(f"Error saving profile image for user {user.id}: {e}", exc_info=True)
        await message.reply(strings.PROFILE_PHOTO.SAVE_PHOTO_FAILED)
        await state.clear()
    except Exception:
        await message.reply(strings.PROFILE_PHOTO.SAVE_PHOTO_FAILED)


@router.message(LoadState.loading_profile_pic)
async def wrong_profile_image(message: aiogram.types.Message):
    kb = await keyboards.inline.get_profile_picture_keyboard()
    await message.answer(strings.PROFILE_PHOTO.LOAD_PHOTO_WRONG_FORMAT, reply_markup=kb)


@router.callback_query(LoadState.loading_profile_pic,
                       keyboards.callback_data.ProfilePictureCallback.filter())
async def cancel_profile_image_loading(query: aiogram.types.CallbackQuery,
                                       state: aiogram.fsm.context.FSMContext,
                                       bot: aiogram.Bot):
    await query.answer()
    await state.clear()
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await query.message.answer(strings.PROFILE_PHOTO.CANCEL_TEXT)


@router.message(aiogram.filters.StateFilter(None), aiogram.F.text)
@router.message(keyboard.MenuState.navigating, aiogram.F.text)
async def other_text_handler(message: types.Message,
                             user: models.user.User,
                             session: sqlalchemy.orm.Session,
                             bot: aiogram.Bot):
    user.requests += 1
    session.add(user)

    active_message_object: types.Message | None = None
    try:
        active_message_object = await message.answer("⏳")
    except TelegramBadRequest:
        await message.answer("Error: Could not start AI response. Try select other model or clear context.")
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
        ai_messages.append({"role": "system", "content": strings.DEFAULT_INSTRUCTIONS + user.instruction})
    else:
        ai_messages.append({"role": "system", "content": strings.DEFAULT_INSTRUCTIONS})

    if user.context_mode_on:
        ai_messages += services.message_service.get_context_messages(session, user)

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
                    logging.info(f"AI API Error {response.status}: {error_text[:500]}")
                    active_message_object = await send_or_update_formatted_message(bot, message.chat.id,
                                                                                   f"AI Error: {response.status}",
                                                                                   active_message_object, False)
                    return

                async for chunk_bytes in response.content.iter_any():
                    if not chunk_bytes:
                        continue
                    # print(chunk_bytes.decode("utf-8", errors="ignore"), end="")

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

                                is_in_think_block = False
                                current_text_segment = ""
                                active_message_object = None
                            else:
                                current_text_segment += processing_buffer
                                print(processing_buffer)
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
                                print(processing_buffer)
                                processing_buffer = ""
                                break

                        if not processing_buffer:
                            break

                    now = asyncio.get_event_loop().time()
                    if len(current_text_segment) > SAFE_MAX_LEN or \
                            (
                                    current_text_segment.strip() and now - last_update_ts > MIN_UPDATE_INTERVAL_SEC):

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
                                active_message_object = None
                        last_update_ts = now

                if processing_buffer:
                    print(processing_buffer)
                    current_text_segment += processing_buffer
                    processing_buffer = ""

                if current_text_segment.strip():
                    active_message_object = await send_or_update_formatted_message(
                        bot=bot, chat_id=message.chat.id, text_content=current_text_segment,
                        current_message_obj=active_message_object, is_think_block_content=is_in_think_block
                    )

        user.successful_requests += 1
        session.add(user)

        await asyncio.sleep(10)
        await send_or_update_formatted_message(
            bot=bot, chat_id=message.chat.id, text_content=current_text_segment,
            current_message_obj=active_message_object, is_think_block_content=is_in_think_block
        )

    except aiohttp.ClientError as e:
        err_msg = "Error: Could not connect to AI service."
        if active_message_object:
            await send_or_update_formatted_message(bot, message.chat.id, err_msg, active_message_object, False)
        else:
            await message.answer(err_msg)
    except TelegramBadRequest as e:
        await message.answer("Error: A problem occurred while displaying the AI response.")
    except Exception as e:
        err_msg = "Error: An unexpected error occurred."
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
