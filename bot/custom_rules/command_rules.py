from typing import TYPE_CHECKING

from twilight_vk.framework.rules import BaseRule
from twilight_vk.utils.types.event_types import BotEventType

if TYPE_CHECKING:
    from modules.assocs import Assoc

class FromUser(BaseRule):

    def __init__(self) -> None:
        '''
        Проверка что сообщение пришло от пользователя (не бота)
        '''
        super().__init__(
            on_event_types = [BotEventType.MESSAGE_NEW, BotEventType.MESSAGE_EVENT]
        )

    async def check(self, event: dict):

        _user_id = event["object"]["message"]["from_id"] if event.get("type") == BotEventType.MESSAGE_NEW else event["object"]["user_id"]

        if _user_id > 0:
            return True
        
        return False

class FromChat(BaseRule):
    
    def __init__(self) -> None:
        '''
        Проверка что сообщение пришло из беседы, а не из личных сообщений
        '''
        super().__init__(
            on_event_types = [BotEventType.MESSAGE_NEW, BotEventType.MESSAGE_EVENT]
        )

    async def check(self, event: dict):

        _peer_id = event["object"]["message"]["peer_id"] if event.get("type") == BotEventType.MESSAGE_NEW else event["object"]["peer_id"]

        if _peer_id > 2000000000:
            return True
        
        return False