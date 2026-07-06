from typing import TYPE_CHECKING, Any

from twilight_vk.framework.rules import BaseRule
from twilight_vk.utils.types.event_types import BotEventType

from modules.assocs import Assoc

if TYPE_CHECKING:
    from utils.db_client import AsyncPGClient
    from modules.database import DarkyDatabase

class IsRegistered(BaseRule):

    def __init__(self) -> None:
        '''
        Проверка что пользователь/чат зарегистрирован в базе данных
        '''
        super().__init__(
            on_event_types = [BotEventType.MESSAGE_NEW, BotEventType.MESSAGE_EVENT]
        )
    
    async def _get_entity(self, event: dict, entity: str = "user") -> bool:

        _data = event.get("chat_data") if entity == "chat" else event.get("user_data")
        return True if _data else False
    
class IsUserRegistered(IsRegistered):
    '''
    Проверка регистрации пользователя в базе данных
    '''
    async def check(self, event: dict) -> bool:
        return await self._get_entity(event, "user")
    
class IsChatRegistered(IsRegistered):
    '''
    Проверка регистрации чата в базе данных
    '''
    async def check(self, event: dict) -> bool:
        return await self._get_entity(event, "chat")
    
class CheckSettings(BaseRule):

    def __init__(self,
                 value: str,
                 key: Any) -> None:
        '''
        Проверка определенных полей в настройках пользователя/чата
        '''
        super().__init__(
            on_event_types = [BotEventType.MESSAGE_NEW, BotEventType.MESSAGE_EVENT],
            value = value,
            key = key
        )
        self.key: str
        self.value: Any
    
    async def _check_setting(self, event: dict, entity: str = "user") -> bool:
        return (event["chat_data"][self.key] == self.value) if entity == "chat" else (event["user_data"][self.key] == self.value)
    
class CheckUserSettings(CheckSettings):
    '''
    Проверка поля в настройках пользователя
    '''
    async def check(self, event: dict) -> bool:
        return await self._check_setting(event, "user")
    
class CheckChatSettings(CheckSettings):
    '''
    Проверка поля в настройках чата
    '''
    async def check(self, event: dict) -> bool:
        return await self._check_setting(event, "chat")