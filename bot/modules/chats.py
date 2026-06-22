from typing import TYPE_CHECKING
import logging

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
        _peer_id = event["object"]["message"]["peer_id"]

        if _peer_id < 2000000000:
            logger.error(f"Chat ID cannot be less than 2000000000")
            return

        logger.debug(f"Checking registration for chat {_peer_id}...")
        if await self._db.check_registration("chat", _peer_id):
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

        logger.info(f"Chat {_peer_id} was registered")
        return f"✅ Ваш чат с ID: {_chat_id} был успешно зарегистрирован"
    
    async def update_timestamp(self, event: dict) -> None:
        '''
        Обновление временной метки чата в базе данных
        '''
        _peer_id = event["object"]["message"]["peer_id"]

        if _peer_id < 2000000000:
            logger.error(f"Chat ID cannot be less than 2000000000")
            return

        logger.debug(f"Checking registration for chat {_peer_id}...")
        if not await self._db.check_registration("chat", _peer_id):
            logger.debug(f"Chat {_peer_id} is not registered")
            return
        
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

        if _peer_id < 2000000000:
            logger.error(f"Chat ID cannot be less than 2000000000")
            return
        
        logger.debug(f"Checking registration for chat {_peer_id}...")
        if not await self._db.check_registration("chat", _peer_id):
            logger.debug(f"Chat {_peer_id} is not registered")
            return

        if _user_id < 0:
            logger.warning(f"{_user_id} is not user")
            return

        logger.debug(f"Checking registration for chat member {_user_id} in {_peer_id}...")
        if await self._db.check_registration_chat_member(_peer_id, _user_id):
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
            " 🔹 Оповещения бота: {_chat.update_notifications}\n" \
            " 🔹 Упоминания в приветствиях: {_chat.mention_in_greetings}\n" \
            " 🔹 Оповещения о новых уровнях: {_chat.lvlups}\n" \
            " 🔹 РП-команды: {_chat.rp}\n" \
            " 🔹 Никнеймы: {_chat.nicknames}\n" \
            " 🔹 Управление РП-командами: {_chat.manage_rp}\n" \
            " 🔹 Управление никнеймами: {_chat.manage_nicknames}\n" \
            " 🔹 Триггеры: {_chat.triggers}\n" \
            " 🔹 Автоисправление раскладки: {_chat.layout_autodetect}\n" \
            " 🔹 Доступ к mute: {_chat.who_can_mute}\n" \
            " 🔹 Доступ к kick: {_chat.who_can_kick}\n" \
            " 🔹 Доступ к предупреждениям: {_chat.who_can_warn}\n" \
            " 🔹 Доступ к банам: {_chat.who_can_ban}\n" \
            " 🔹 Лимит предупреждений: {_chat.warns_limit}\n" \
            " 🔹 Наказание за лимит предупреждений: {_chat.warn_punishment}\n" \
            " 🔹 Автокик: {_chat.autokick}\n" \
            "🛡 Настройки системы DarkyVerify:\n" \
            " 🔹 Статус: {_chat.verify_enabled}\n" \
            " 🔹 Наказание: {_chat.verify_punishment}\n" \
            " 🔹 Дней с регистрации должно пройти: {_chat.days_from_signup}\n" \
            " 🔹 Должны быть подписаны на группы: {_chat.should_follow_groups}\n" \
            " 🔹 Спам-защита: {_chat.spam_detection}"
        )


    async def show_chat_member(self, event: dict, member_id: int):
        '''
        Отображает данные участника беседы
        '''
        pass
    
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