from twilight_vk.utils.keyboard import (
    KeyboardMarkup,
    CallbackActionKeyboardButton
)
from twilight_vk.utils.types.keyboard_colors import KeyboardColor


class Links:

    HELP_LINK = None
    GET_STARTED_LINK = None

class Replies:

    BOT_GREETING = (
        "❤️Спасибо за добавление в беседу❤️\n"
        "\n"
        "Меня зовут Дарки и я бот, предназначенный для администрирования бесед и развлечения.\n"
        "У меня есть множество команд и гибких настроек позволяющих настроить мое поведение на ваш вкус\n"
        "\n"
        "❗️Для полного функционала Ваш чат необходимо зарегистрировать - "
        "для этого сделайте меня администратором этой беседы и напишите команду \"$darky reg\", "
        "либо же нажмите яркую кнопочку снизу с надписью \"Зарегистрировать чат\", а дальше я все сделаю сама.\n"
        "\n"
        f"❕Подробную инструкцию по регистрации беседы вы можете посмотреть здесь {Links.GET_STARTED_LINK}\n"
        "\n"
        "❕Помощь по использованию бота можно получить введя команду \"$darky help\", либо нажав на кнопочку ниже с названием \"Руководство бота\"\n"
        "\n"
        "❤️Приятного пользования и времяпровождения :3❤️",
        "photo-192784148_457239358",
        KeyboardMarkup(
            inline=True,
            buttons = [
                [
                    CallbackActionKeyboardButton(
                        label = "Зарегистрировать чат",
                        payload = "{\"request\":\"chat_register\"}",
                        color = KeyboardColor.PRIMARY
                    )
                ],
                [
                    CallbackActionKeyboardButton(
                        label = "Руководство бота",
                        payload = "{\"request\":\"get_help\"}",
                        color = KeyboardColor.SECONDARY
                    )
                ]
            ]
        )
    )

    HELP = (
        f"❔ Руководство по использованию бота вы можете прочитать здесь: {Links.HELP_LINK}",
        None,
        None
    )