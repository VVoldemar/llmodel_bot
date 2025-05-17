import aiogram

from models.user import User


GREETING = '''
Hi, I'm AI bot
'''

def profile_info(user: User):
    return f"""
*👤 {user.username}*

Register date: {str(user.registered_at).split()[0]}
Sent requests: {user.requests}
Successful requests: {user.successful_requests}
Referrals: {len(user.referrals)}
"""


async def promo(user: User, bot: aiogram.Bot):
    bot_info = await bot.get_me()
    return f"""
Отправьте друзьям эту ссылку:
https://t.me/{bot_info.username}?start={user.id}

Она сработает, только если они не взаимодействовали с ботом до этого
"""


class MENU_KEYBOARD:
    PROFILE = "👤 Профиль"
    MODEL = "🧰 Выбрать ИИ модель"
    HELP = "🆘 Поддержка"
    REFERRAL = "🔗 Привести друга"
    SETTINGS = "📜 Настройки"


class PROFILE_PHOTO:
    LOAD_PHOTO_TEXT = "Load profile photo. As photo, not as file"
    LOAD_PHOTO_WRONG_FORMAT = "You haven't uploaded photo file yet. Load it as a photo, not a file"
    SAVE_PHOTO_SUCCESS = "✅ Photo saved successfully"
    SAVE_PHOTO_FAILED = "❌ Photo wasn't saved, unexpected error occurred. Try again."
    CANCEL_TEXT = "Profile picture loading cancelled"

    CANCEL_LOADING = "Cancel"
    CANCEL_CALLBACK = "cancel"


DEFAULT_INSTRUCTIONS = """Please note:
Markdown entities must not be nested.
To escape characters '_', '*', '`', '[' outside of an entity, prepend the characters '\\' before them."""

CHANGE_MODEL_TEXT = "Select preferable model. If model doesn't respond, try clear context or select another one."
MODELS = {
    "qwen3-235b-a22b": "Qwen 3 235B",
    "llama-4-maverick": "Llama 4 Maverick",
    "deepseek-r1": "DeepSeek R1",
    "deepseek-v3": "DeepSeek V3"
}

MODEL_SELECTED = "✅ "


class SETTINGS_MENUS:
    BACK = "< Back"
    ACTION_BACK = "back"

    # MENU_SET_INSTRUCTION = 

    class DESCRIPTION:
        MENU_MAIN = """*Settings*
        
        In this section, you can:
        1. Assign any role or custom instruction the bot will consider when preparing responses.
        2. Turn context maintenance on or off. When the context is on, the bot considers its previous response to conduct a dialogue.
        3. Select the interface language."""
        MENU_INSTRUCTION = "*Instruction Settings*\n\nIn this section, you can assign any role or instruction, which the bot will follow when preparing responses.\n\n"
        MENU_CONTEXT = "*Context Settings*\n\nThis affects an AI's ability to view dialog history"
        MENU_LANGUAGE = "*Language Settings*\n\nSelect language inteface"
        MENU_SET_INSTRUCTION = "Write and send your instructions.\n\nFor example, translate all requests into Spanish"

    class MENU_MAIN:
        INSTRUCTION = "Set custom instruction"
        CONTEXT = "Context maintenance"
        LANGUAGE = "Language"

        CALLBACK_INSTRUCTION = "settings_instruction"
        CALLBACK_CONTEXT = "settings_context"
        CALLBACK_LANGUAGE = "settings_language"

    class MENU_INSTRUCTION:
        EDIT = "Edit Custom Instruction"
        CHANGE_MODE = "Instruction Mode on/off"
        MODE_ON = "✅ Instruction Mode ON/off"
        MODE_OFF = "❌ Instruction Mode on/OFF"

        CALLBACK_EDIT = "action_edit_instruction"
        CALLBACK_CHANGE_MODE = "action_onoff_instruction"

        CALLBACK_MENU_SET_INSTRUCTION = "settings_set_instruction"

        INSTRUCTION_NOT_ASSIGNED = "Custom instructions: not assigned"
        INSTRUCTION_ASSIGNED_HEADER = "instructions:"
        INSTRUCTION_UPDATED = "✅ *Instruction seccessfully updated*\n\nCurrent role: "

    class MENU_CONTEXT:
        CONTEXT_ON = "Enable Context"
        CONTEXT_OFF = "Disable Context"

        CALLBACK_CONTEXT_ON = "action_set_lang_en"
        CALLBACK_CONTEXT_OFF = "action_set_lang_ru"

        CONTEXT_SELECTED = "✅ "

    class MENU_LANGUAGE:
        ENGLISH = "Set English"
        RUSSIAN = "Set Russian"

        CALLBACK_ENGLISH = "action_set_lang_en"
        CALLBACK_RUSSIAN = "action_set_lang_ru"


class CLEAR_CONTEXT:
    SUCESS = "✅ Context successfully cleared. AI wouldn't see messages above."
    ERROR = "❌ Context clearing has failed. Try again."