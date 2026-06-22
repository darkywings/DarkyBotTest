from typing import TYPE_CHECKING

from twilight_vk.framework.rules import (
    BaseRule,
)

if TYPE_CHECKING:
    from modules.database import DarkyDatabase

class IsBotAdmin(BaseRule):

    def __init__(self,
                 db: "DarkyDatabase") -> None:
        '''
        Проверяет является ли пользователь администратором бота
        '''
        super().__init__(
            db = db
        )
        self.db: "DarkyDatabase"

    async def _getAdmins(self, event: dict):
        
        if event.setdefault("darkybot_admin", None) is None:
            _user_id = event["object"]["message"]["from_id"]
            event["darkybot_admin"] = await self.db.is_bot_admin(_user_id)

    async def check(self, event: dict) -> bool:
        
        await self._getAdmins(event)       
        return event.get("darkybot_admin")