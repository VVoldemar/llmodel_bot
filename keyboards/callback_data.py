import aiogram.filters.callback_data
# import models.subscription

class SettingsCallback(aiogram.filters.callback_data.CallbackData, prefix="settings"):
    action: str

class ModelCallback(aiogram.filters.callback_data.CallbackData, prefix="model", sep="|"):
    model: str