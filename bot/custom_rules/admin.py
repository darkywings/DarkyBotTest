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

    async def check(self, event: dict) -> bool:
        
        _user_id = event["object"]["message"]["from_id"]

        if await self.db.is_user_bot_admin(_user_id):
            return True
        
        return False