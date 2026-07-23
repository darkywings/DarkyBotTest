from twilight_vk.utils.keyboard import (
    KeyboardMarkup,
    CallbackActionKeyboardButton
)
from twilight_vk.utils.types.keyboard_colors import KeyboardColor


class Links:

    HELP_LINK = None
    GET_STARTED_LINK = None

class Buttons:

    REG_CHAT = CallbackActionKeyboardButton(
        label = "Зарегистрировать чат",
        payload = "{\"darky_button\":\"reg_chat\"}",
        color = KeyboardColor.PRIMARY
    )

    GET_HELP = CallbackActionKeyboardButton(
        label = "Руководство бота",
        payload = "{\"darky_button\":\"help\"}",
        color = KeyboardColor.SECONDARY
    )

    SPEAK_HELP = CallbackActionKeyboardButton(
        label = "Как пользоваться DarkySpeak?",
        payload = "{\"darky_button\":\"speak_help\"}",
        color = KeyboardColor.SECONDARY
    )

class Replies:

    BOT_GREETING = (
        "❤️ Спасибо за добавление в беседу❤️\n"
        "\n"
        "Меня зовут Дарки и я бот, предназначенный для администрирования бесед и развлечения.\n"
        "У меня есть множество команд и гибких настроек позволяющих настроить мое поведение на ваш вкус\n"
        "\n"
        "❗️ Для полного функционала Ваш чат необходимо зарегистрировать - "
        "для этого сделайте меня администратором этой беседы и напишите команду \"$darky reg\", "
        "либо же нажмите яркую кнопочку снизу с надписью \"Зарегистрировать чат\", а дальше я все сделаю сама.\n"
        "\n"
        f"❕ Подробную инструкцию по регистрации беседы вы можете посмотреть здесь {Links.GET_STARTED_LINK}\n"
        "\n"
        "❕ Помощь по использованию бота можно получить введя команду \"$darky help\", либо нажав на кнопочку ниже с названием \"Руководство бота\"\n"
        "\n"
        "❤️ Приятного пользования и времяпровождения :3❤️",
        "photo-192784148_457239358",
        KeyboardMarkup(
            inline = True,
            buttons = [
                [Buttons.REG_CHAT],
                [Buttons.GET_HELP]
            ]
        )
    )

    HELP = (
        f"❔ Руководство по использованию бота вы можете прочитать здесь: {Links.HELP_LINK}",
        None,
        None
    )

    WITLESS_GENERATE_FAIL = (
        "🥺 Я попыталась сгенерировать сообщение, но у меня ничего не получилось.\n\n"
        "Обычно это связано с тем, что я собрала недостаточно данных для генерации, либо же вам просто не повезло и вы можете повторить попытку.\n"
        "❕  На всякий случай убедитесь, что вы выдали мне доступ ко всей переписке и продолжайте общаться <3",
        None,
        KeyboardMarkup(
            inline = True,
            buttons = [
                [Buttons.SPEAK_HELP]
            ]
        )
    )

    WITLESS_ON_INFO = (
        None,
        None,
        KeyboardMarkup(
            inline = True,
            buttons = [
                [
                    CallbackActionKeyboardButton(
                        label = "Сгенерировать",
                        payload = "{\"darky_button\":\"speak_again\"}",
                        color = KeyboardColor.PRIMARY
                    )
                ],
                [Buttons.SPEAK_HELP]
            ]
        )
    )

    UNKNOWN_ERROR = (
        "❌ Произошла неизвестная ошибка O~O",
        None,
        None
    )

    NOT_WORK_HERE = (
        "⚠️ Эта команда здесь не работает",
        None,
        KeyboardMarkup(
            inline=True,
            buttons=[
                [Buttons.GET_HELP]
            ]
        )
    )

    DISABLED = (
        "❌ Данная команда была выключена разработчиком",
        None,
        KeyboardMarkup(
            inline=True,
            buttons=[
                [Buttons.GET_HELP]
            ]
        )
    )

    UNDER_DEVELOPMENT = (
        "⚠️ Данная команда находится в разработке",
        None,
        KeyboardMarkup(
            inline=True,
            buttons=[
                [Buttons.GET_HELP]
            ]
        )
    )

    ACCESS_DENIED = (
        "⛔ В доступе отказано.\n" \
        "Вы не являетесь администратором беседы или бота",
        None,
        KeyboardMarkup(
            inline=True,
            buttons=[
                [Buttons.GET_HELP]
            ]
        )
    )

    BOT_IS_NOT_ADMIN = (
        "⚠️ Я не могу выполнить эту команду без прав администратора.\n"
        "Пожалуйста, выдайте их мне и повторите попытку",
        None,
        KeyboardMarkup(
            inline=True,
            buttons=[
                [Buttons.GET_HELP]
            ]
        )
    )

    WRONG_USAGE = (
        "⚠️ Некорректное использование команды.\n"
        "Убедитесь, что вы правильно ввели команду, её аргументы и повторите попытку",
        None,
        KeyboardMarkup(
            inline=True,
            buttons=[
                [Buttons.GET_HELP]
            ]
        )
    )

    CHAT_IS_NOT_REGISTERED = (
        "❗️ Для полного функционала Ваш чат необходимо зарегистрировать - "
        "для этого сделайте меня администратором этой беседы и напишите команду \"$darky reg\", "
        "либо же нажмите яркую кнопочку снизу с надписью \"Зарегистрировать чат\", а дальше я все сделаю сама.\n"
        "\n"
        f"❕ Подробную инструкцию по регистрации беседы вы можете посмотреть здесь {Links.GET_STARTED_LINK}\n"
        "\n"
        "❕ Помощь по использованию бота можно получить введя команду \"$darky help\", либо нажав на кнопочку ниже с названием \"Руководство бота\"\n",
        None,
        KeyboardMarkup(
            inline = True,
            buttons = [
                [Buttons.REG_CHAT],
                [Buttons.GET_HELP]
            ]
        )
    )

    DISABLED_BY_ADMIN = (
        "❌ Данная команда была выключена администраторами беседы в настройках чата.\n",
        None,
        KeyboardMarkup(
            inline=True,
            buttons=[
                [Buttons.GET_HELP]
            ]
        )
    )
