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

        logger.debug(f"Checking registration for chat {_peer_id}...")
        if await self._db.check_registration("chat", _peer_id):
            logger.debug(f"Chat {_peer_id} is already registered")
            return f"⚠️Ваш чат уже был ранее зарегистрирован"
        
        logger.debug(f"Registering chat {_peer_id}...")
        _chat = await self._methods.messages.getConversationById(
            peer_ids = _peer_id
        )
        _chat = _chat["response"]["items"][0]

        _chat_members = await self._methods.messages.getConversationMembers(
            peer_id = _peer_id
        )
        _chat_members = _chat_members["response"]["items"]

        _chat_id = _chat["peer"]["id"]
        _chat_title = _chat["chat_settings"]["title"]

        await self._db.register_chat(_chat_id, _chat_title, _chat_members)

        logger.info(f"Chat {_peer_id} was registered")
        return f"✅Ваш чат с ID: {_chat_id} был успешно зарегистрирован"
    
    async def reg_chat_member(self, event: dict) -> None:
        '''
        Регистрация участника в чате при каждом новом сообщении
        если до этого он не был зарегистрирован
        '''
        _user_id = event["object"]["message"]["from_id"]
        _peer_id = event["object"]["message"]["peer_id"]

        logger.debug(f"Checking registration for chat member {_user_id} in {_peer_id}...")
        if await self._db.check_registration_chat_member(_peer_id, _user_id):
            logger.debug(f"Chat member {_user_id} is already registered in chat {_peer_id}")
            return
        
        logger.debug(f"Registering chat_member {_user_id} in chat {_peer_id}...")
        await self._db.reg_chat_member(_peer_id, _user_id)

        logger.info(f"Chat member {_user_id} was registered in chat {_peer_id}")