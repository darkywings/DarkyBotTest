from typing import TYPE_CHECKING, Any

from twilight_vk.framework.rules import BaseRule
from twilight_vk.utils.types.event_types import BotEventType

from modules.assocs import Assoc

if TYPE_CHECKING:
    from utils.db_client import AsyncPGClient
    from modules.database import DarkyDatabase

class IsRegistered(BaseRule):

    def __init__(self, db: "DarkyDatabase") -> None:
        '''
        Проверка что чат зарегистрирован в базе данных
        '''
        super().__init__(
            on_event_types = [BotEventType.MESSAGE_NEW, BotEventType.MESSAGE_EVENT],
            _db = db
        )
        self._db: "DarkyDatabase"

    async def check(self, event: dict) -> bool:

        _peer_id = event["object"]["message"]["peer_id"] if event.get("type") == BotEventType.MESSAGE_NEW else event["object"]["peer_id"]
        return await self._db.get_chat(_peer_id) if _peer_id > 2000000000 else await self._db.get_user(_peer_id)
    
class SQLRule(BaseRule):
    
    def __init__(self,
                 asyncpg: "AsyncPGClient",
                 query: str,
                 key: str,
                 value) -> None:
        '''
        Проверка поля таблицы по SQL запросу

        :param key: Поле для проверки
        :type key: str

        :param value: Ожидаемое значение поля key
        :type value: Any
        '''
        super().__init__(
            on_event_types = [BotEventType.MESSAGE_NEW, BotEventType.MESSAGE_EVENT],
            _db = asyncpg,
            _query = query,
            _key = key,
            _value = value
        )
        self._db: "AsyncPGClient"
        self._query: str
        self._key: str
        self._value: Any

    async def check(self, event: dict) -> bool:

        if "SELECT" not in self._query:
            return False

        _user_id = event["object"]["message"]["from_id"] if event.get("type") == BotEventType.MESSAGE_NEW else event["object"]["user_id"]
        _chat_id = event["object"]["message"]["peer_id"] if event.get("type") == BotEventType.MESSAGE_NEW else event["object"]["peer_id"]
        
        self._query = (
            self._query
            .replace("<user_id_check>", f"user_id = {_user_id}")
            .replace("<chat_id_check>", f"chat_id = {_chat_id}")
        )

        result = await self._db.fetchrow(self._query)
        
        if not result:
            return False
        
        return result[self._key] == self._value