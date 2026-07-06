from typing import TYPE_CHECKING

from twilight_vk.framework.rules import (
    BaseRule,
)
from twilight_vk.utils.types.event_types import BotEventType

if TYPE_CHECKING:
    from modules.database import DarkyDatabase

class IsBotAdmin(BaseRule):

    def __init__(self) -> None:
        '''
        Проверяет является ли пользователь администратором бота
        '''
        super().__init__(
            on_event_types = [BotEventType.MESSAGE_NEW, BotEventType.MESSAGE_EVENT]
        )

    async def check(self, event: dict) -> bool:
        
        is_admin: bool = event.get("darkybot_admin")
        return is_admin if isinstance(is_admin, bool) else False