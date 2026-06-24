from typing import TYPE_CHECKING
import logging

from twilight_vk.utils.config import CONFIG as twi_config
from twilight_vk.utils.types.event_types import BotEventType

if TYPE_CHECKING:
    from twilight_vk.framework.methods import VkMethods
    from modules.database import DarkyDatabase

logger = logging.getLogger("bot-chats")

class Chats:

    def __init__(self,
                 db_client: "DarkyDatabase",
                 methods: "VkMethods"
                 ) -> None:
        self._db = db_client
        self._methods = methods
    
    async def reg_chat(self, event: dict) -> str:
        '''
        Регистрация чата в базе данных
        '''
        _peer_id = event["object"]["message"]["peer_id"] if event["type"] == BotEventType.MESSAGE_NEW else event["object"]["peer_id"]

        if _peer_id < 2000000000:
            logger.error(f"Chat ID cannot be less than 2000000000")
            return

        logger.debug(f"Checking registration for chat {_peer_id}...")
        if await self._db.get_chat(_peer_id):
            logger.debug(f"Chat {_peer_id} is already registered")
            return f"⚠️ Ваш чат уже был ранее зарегистрирован"
        
        logger.debug(f"Registering chat {_peer_id}...")
        _chat = await self._methods.messages.getConversationById(
            peer_ids = _peer_id
        )
        _chat = _chat["response"]["items"][0]

        _chat_members = await self._methods.messages.getConversationMembers(
            peer_id = _peer_id
        )
        _chat_members = _chat_members["response"]["profiles"]

        _chat_id = _chat["peer"]["id"]
        _chat_title = _chat["chat_settings"]["title"]

        await self._db.register_chat(_chat_id, _chat_title, _chat_members)

        await self._methods.messages.base_api.base_get_method(
            api_method = "messages.sendMessageEventAnswer",
            values = {
                "event_id": event["object"]["event_id"],
                "user_id": event["object"]["user_id"],
                "peer_id": event["object"]["peer_id"],
                "v": self._methods.messages.__api_version__
            }
        )

        logger.info(f"Chat {_peer_id} was registered")
        return f"✅ Ваш чат с ID: {_chat_id} был успешно зарегистрирован"
    
    async def update_timestamp(self, event: dict) -> None:
        '''
        Обновление временной метки чата в базе данных
        '''
        _peer_id = event["object"]["message"]["peer_id"]
        
        logger.debug(f"Updating timestamp for chat {_peer_id}...")
        await self._db.update_chat_timestamp(_peer_id)
        logger.debug(f"Timestamp for chat {_peer_id} updated")
    
    async def reg_chat_member(self, event: dict) -> None:
        '''
        Регистрация участника в чате при каждом новом сообщении
        если до этого он не был зарегистрирован
        '''
        _user_id = event["object"]["message"]["from_id"]
        _peer_id = event["object"]["message"]["peer_id"]

        if _user_id < 0:
            logger.warning(f"{_user_id} is not user")
            return

        logger.debug(f"Checking registration for chat member {_user_id} in {_peer_id}...")
        if await self._db.get_chat_member(_peer_id, _user_id):
            logger.debug(f"Chat member {_user_id} is already registered in chat {_peer_id}")
            return
        
        logger.debug(f"Registering chat_member {_user_id} in chat {_peer_id}...")
        await self._db.reg_chat_member(_peer_id, _user_id)

        logger.info(f"Chat member {_user_id} was registered in chat {_peer_id}")
    
    async def show_chat(self, event: dict) -> str:
        '''
        Отображает данные беседы и ее настройки
        '''
        _peer_id = event["object"]["message"]["peer_id"]

        logger.debug(f"Getting the chat {_peer_id} info...")
        _chat = await self._db.get_chat(_peer_id)
        logger.debug(f"Chat {_peer_id} info was got")

        return (
            "🧾 Информация о чате:\n" \
            f" 🔹 ID чата: {_chat["chat_id"]}\n" \
            f" 🔹 ID чата в боте: {_chat["id"]}\n" \
            f" 🔹 Название чата: {_chat["chat_title"]}\n" \
            f" 🔹 Количество РП команд: {_chat["rp_count"]}\n" \
            f" 🔹 Количество зарегистрированных участников: {_chat["members_count"]}\n" \
            f" 🔹 Дата регистрации в боте: {_chat["created_at"]}\n" \
            "⚙️ Настройки чата:\n" \
            f" 🔹 Оповещения бота: {_chat["update_notifications"]}\n" \
            f" 🔹 Упоминания в приветствиях: {_chat["mention_in_greetings"]}\n" \
            f" 🔹 Оповещения о новых уровнях: {_chat["lvlups"]}\n" \
            f" 🔹 РП-команды: {_chat["rp"]}\n" \
            f" 🔹 Никнеймы: {_chat["nicknames"]}\n" \
            f" 🔹 Управление РП-командами: {_chat["manage_rp"]}\n" \
            f" 🔹 Управление никнеймами: {_chat["manage_nicknames"]}\n" \
            f" 🔹 Триггеры: {_chat["triggers"]}\n" \
            f" 🔹 Автоисправление раскладки: {_chat["layout_autodetect"]}\n" \
            f" 🔹 Доступ к запрету сообщений: {_chat["who_can_mute"]}\n" \
            f" 🔹 Доступ к исключению пользователей: {_chat["who_can_kick"]}\n" \
            f" 🔹 Доступ к предупреждениям: {_chat["who_can_warn"]}\n" \
            f" 🔹 Доступ к банам: {_chat["who_can_ban"]}\n" \
            f" 🔹 Лимит предупреждений: {_chat["warn_limit"]}\n" \
            f" 🔹 Наказание за лимит предупреждений: {_chat["warn_punishment"]}\n" \
            f" 🔹 Автокик: {_chat["autokick"]}\n" \
            "🛡 Настройки системы DarkyVerify:\n" \
            f" 🔹 Статус: {_chat["verify_enabled"]}\n" \
            f" 🔹 Наказание: {_chat["verify_punishment"]}\n" \
            f" 🔹 Дней с регистрации должно пройти: {_chat["days_from_signup"]}\n" \
            f" 🔹 Должны быть подписаны на группы: {_chat["should_follow_groups"]}\n" \
            f" 🔹 Спам-защита: {_chat["spam_detection"]}"
            .replace("True", "✅")
            .replace("False", "❌")
            .replace("all", "❕ Все пользователи ❕")
            .replace("nobody", "❌ Никто ❌")
            .replace("admins", "❗️ Только администраторы ❗️")
            .replace("none", "❌ Не установлено ❌")
            .replace("mute", "❕ Запрет на сообщения ❕")
            .replace("kick", "❕ Исключение ❕")
            .replace("ban", "❗️ Бан ❗️")
        )


    async def show_chat_member(self, event: dict, member_id: int):
        '''
        Отображает данные участника беседы
        '''

        # TODO: ЗДЕСЬ ДОЛЖНА БЫТЬ ЕЩЕ КАРТИНКА СТАТИСТИКИ ОТРЕНДЕРЕННАЯ С ГРАФИКОМ АКТИВНОСТИ И ТЕКУЩЕГО УРОВНЯ
        _peer_id = event["object"]["message"]["peer_id"]

        if member_id == -event["group_id"]:
            
            _bot_stats = await self._db.get_bot_stats()
            return (
                "📊 Статистика Дарки-бота:\n" \
                f" 🔹 Работает и разрабатывается с 9 марта 2020 года.\n" \
                f" 🔹 Версия бота: {_bot_stats["version"]}\n" \
                f" 🔹 Версия фреймворка TWILIGHT: {twi_config.FRAMEWORK.version}\n" \
                f" 🔹 Последнее обновление получено: {_bot_stats["last_update"]}\n" \
                f" 🔹 Создатель бота и фреймворка: {twi_config.FRAMEWORK.developer}\n" \
                f" 🔹 Зарегистрировано бесед: {_bot_stats["chats_total"]}\n" \
                f" 🔹 Зарегистрировано пользователей {_bot_stats["users_total"]}\n" \
                f" 🔹 Обработано запросов: {_bot_stats["requests_handled"]}"
            )

        if member_id < 0:
            return "⚠️ Я не собираю статистику и не регистрирую других ботов в своей базе, у меня нет необходимости делать это"
        
        logger.debug(f"Getting the chat {_peer_id} member {member_id} info...")
        _member = await self._db.get_chat_member_stats(_peer_id, member_id)
        logger.debug(f"Chat {_peer_id} member {member_id} info was got")

        return (
            "📊 Статистика участника беседы:\n" \
            f" 🔹 ID пользователя: {_member["user_id"]}\n" \
            f" 🔹 Забанен: {_member["is_banned"]}\n" \
            f" 🔹 Никнейм: {_member["nickname"]}\n" \
            f" 🔹 Место в топе беседы: {_member["top_place"]} / {_member["total_top"]}\n" \
            f" 🔹 Уровень: {_member["level"]}\n" \
            f" 🔹 Опыт: {_member["xp_per_level"]} exp. / {_member["max_xp_per_level"]} exp.\n" \
            f" 🔹 Всего опыта: {_member["level_xp"]}\n" \
            f" 🔹 Предупреждения: {_member["warns"]}\n" \
            f" 🔹 Количество сообщений: {_member["messages"]}\n" \
            f" 🔹 Количество нецензурных слов: {_member["bad_words"]}\n" \
            f" 🔹 Количество отправленных фотографий: {_member["photo"]}\n" \
            f" 🔹 Количество отправленных видео: {_member["video"]}\n" \
            f" 🔹 Количество отправленных аудиозаписей: {_member["audio"]}\n" \
            f" 🔹 Количество отправленных документов: {_member["docs"]}\n" \
            f" 🔹 Количество голосовых сообщений: {_member["audio_messages"]}\n" \
            "[DEV_NOTE]: Здесь должна быть еще картинка с диаграммой активности и отображением прогресс бара для уровня участника"
        )
    
    async def update_member(self, event: dict, key: str, value: str):
        '''
        Обновляет данные участника беседы
        '''
        pass

    async def update_chat(self, event: dict, key: str, value: str):
        '''
        Обновляет данные чата
        '''
        pass