from typing import TYPE_CHECKING

from twilight_vk.framework.rules import BaseRule

from utils.replies import Replies

if TYPE_CHECKING:
    from modules.database import DarkyDatabase

class FromUser(BaseRule):
    '''
    Проверка что сообщение пришло от пользователя (не бота)
    '''
    async def check(self, event: dict):

        _user_id = event["object"]["message"]["from_id"]

        if _user_id > 0:
            return True
        
        return False

class FromChat(BaseRule):
    '''
    Проверка что сообщение пришло из беседы, а не из личных сообщений
    '''
    async def check(self, event: dict):

        _peer_id = event["object"]["message"]["peer_id"]

        if _peer_id > 2000000000:
            return True
        
        return False
    
class IsRegistered(BaseRule):

    def __init__(self, db: "DarkyDatabase") -> None:
        '''
        Проверка что чат зарегистрирован в базе данных
        '''
        super().__init__(
            _db = db
        )
        self._db: "DarkyDatabase"

    async def check(self, event: dict) -> bool:

        _peer_id = event["object"]["message"]["peer_id"]

        # return await self._db.check_registration(
        #     "chat" if _peer_id > 2000000000 else "user",
        #     _peer_id
        # )

class Disabled(BaseRule):
    '''
    "Отключает" функцию с этим правилом и оповещает об этом пользователя
    '''

    async def check(self, event: dict):

        _peer_id = event["object"]["message"]["peer_id"]
        _conversation_message_id = event["object"]["message"]["conversation_message_id"]
        await self.methods.messages.send(peer_id = _peer_id,
                                         forward={
                                             "is_reply": True,
                                             "peer_id": _peer_id,
                                             "conversation_message_ids": _conversation_message_id
                                         },
                                         message = Replies.DISABLED[0],
                                         keyboard = Replies.DISABLED[2])
        return False

class UnderDevelopment(BaseRule):
    '''
    "Отключает" функцию с этим правилом и оповещает о том, что команда в разработке
    '''

    async def check(self, event: dict):

        _peer_id = event["object"]["message"]["peer_id"]
        _conversation_message_id = event["object"]["message"]["conversation_message_id"]
        await self.methods.messages.send(peer_id = _peer_id,
                                         forward={
                                             "is_reply": True,
                                             "peer_id": _peer_id,
                                             "conversation_message_ids": _conversation_message_id
                                         },
                                         message = Replies.UNDER_DEVELOPMENT[0],
                                         keyboard = Replies.UNDER_DEVELOPMENT[2])
        return False