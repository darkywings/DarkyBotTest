from typing import TYPE_CHECKING

from twilight_vk.framework.rules import BaseRule

if TYPE_CHECKING:
    from utils.db_client import AsyncPGClient
    from modules.database import DarkyDatabase

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
            _db = asyncpg,
            _query = query,
            _key = key,
            _value = value
        )
        self._db: "AsyncPGClient"
        self._query: str

    async def check(self, event: dict) -> bool:

        if "SELECT" not in self._query:
            return False

        _user_id = event["object"]["message"]["from_id"]
        _chat_id = event["object"]["message"]["peer_id"]
        
        self._query = (
            self._query
            .replace("<user_id_check>", f"user_id = {_user_id}")
            .replace("<chat_id_check>", f"chat_id = {_chat_id}")
        )

        result = await self._db.fetchrow(self._query)
        
        if not result:
            return False
        
        return result[self._key] == self._value