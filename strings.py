GREETING = '''
Hi, I'm AI bot
'''

class MENU_KEYBOARD:
    PROFILE = "👤 Профиль"
    MODEL = "🧰 Выбрать ИИ модель"
    HELP = "🆘 Поддержка"
    REFERRAL = "🔗 Привести друга"
    SETTINGS = "📜 Настройки"


# class SETTINGS_KEYBOARD:
#     INSTRUCTION = "Set custom instruction"
#     CONTEXT = "Context maintenance"
#     LANGUAGE = "Language"


MODELS = {
    "gemma-4b-it": "Gemma 4B",
    "llama-4-maverick": "Llama 4 Maverick",
    "deepseek-r1:free": "DeepSeek R1",
    "qwen3-30b-a3b": "Qwen 3 30B"
}

# SETTINGS_MENUS = {
#     MENU_MAIN: [
#         (strings.SETTINGS_KEYBOARD.INSTRUCTION, MENU_INSTRUCTION),
#         (strings.SETTINGS_KEYBOARD.CONTEXT, MENU_CONTEXT),
#         (strings.SETTINGS_KEYBOARD.LANGUAGE, MENU_LANGUAGE),
#     ],
#     MENU_INSTRUCTION: [
#         # Example sub-menu items
#         ("Edit Custom Instruction", "action_edit_instruction"), 
#         ("Instruction Mode on/off", "action_onoff_instruction"),
#         ("Back", ACTION_BACK) 
#     ],
#     MENU_CONTEXT: [
#         # Example sub-menu items
#         ("Enable Context", "action_enable_context"),
#         ("Disable Context", "action_disable_context"),
#         ("Back", ACTION_BACK)
#     ],
#     MENU_LANGUAGE: [
#         # Example sub-menu items
#         ("Set English", "action_set_lang_en"),
#         ("Set Russian", "action_set_lang_ru"),
#         ("Back", ACTION_BACK)
#     ]
#     # Add more menus and sub-menus as needed
# }

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
        MENU_INSTRUCTION = "*Instruction Settings*\n\nIn this section, you can assign any role or instruction, which the bot will follow when preparing responses.\n\nCustom instruction: "
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

        CALLBACK_EDIT = "action_edit_instruction"
        CALLBACK_CHANGE_MODE = "action_onoff_instruction"

        INSTRUCTION_NOT_ASSIGNED = "not assigned"
        INSTRUCTION_UPDATED = "✅ *Instruction seccessfully updated*\n\nCurrent role: "


    class MENU_CONTEXT:
        CONTEXT_ON = "Enable Context"
        CONTEXT_OFF = "Disable Context"

        CALLBACK_CONTEXT_ON = "action_set_lang_en"
        CALLBACK_CONTEXT_OFF = "action_set_lang_ru"

    class MENU_LANGUAGE:
        ENGLISH = "Set English"
        RUSSIAN = "Set Russian"

        CALLBACK_ENGLISH = "action_set_lang_en"
        CALLBACK_RUSSIAN = "action_set_lang_ru"