import os
import logging
from dotenv import load_dotenv

from ..utils.db_client import AsyncPGClient

logger = logging.getLogger("db-client")

load_dotenv()

class DarkyDatabase:

    def __init__(self):
        logger.debug(f"Connecting to the database...")
        self._db_client: AsyncPGClient = AsyncPGClient(
            dsn = f"postgresql://{os.getenv("POSTGRES_BOT_USER")}:{os.getenv("POSTGRES_BOT_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("POSTGRES_BOT_DB")}"
        )
        logger.debug("Database is connected")

    async def check_registration(self,
                                 obj_type: str,
                                 obj_id: int,
                                 only_bool: bool = True) -> dict | bool:
        '''
        Проверка регистрации пользователя или чата в базе данных
        Возвращает найденный объект при наличии иначе False
        '''
        if type not in ["user", "chat"]:
            raise ValueError("type should be only have values \"user\" or \"chat\"")
        
        logger.debug(f"Checking registration for {obj_id}...")

        query = f"SELECT * FROM {obj_type}s WHERE {obj_type}_id = $1"
        record: dict = await self._db_client.fetchrow(query, obj_id)

        if not record:
            logger.debug(f"{obj_id} not found")
            return False
        
        logger.debug(f"{obj_id} was found in database!")
        
        if only_bool:
            return True
        
        _record_dict: dict = None
        for key, value in record.items():
            _record_dict.setdefault(key, value)
        
        return _record_dict
    
    async def register_user(self,
                            user_id: int):
        '''
        Регистрация пользователя в базе данных
        Происходит автоматически при каждом новом сообщении от этого пользователя
        '''
        logger.debug(f"Registering user {user_id} in database table USERS...")
        await self._db_client.execute("""INSERT INTO users (user_id) VALUES ($1);""",
                               user_id)
        logger.debug(f"User {user_id} was added to the database")
    
    async def register_chat(self,
                            peer_id: int,
                            title: str):
        '''
        Регистрация чата в базе данных
        Происходит только после вызова определенной команды
        '''
        logger.debug(f"Registering chat {peer_id} in database table CHATS...")
        await self._db_client.execute("""INSERT INTO chats (chat_id, chat_title) VALUES ($1, $2);""",
                                      peer_id, title)
        logger.debug(f"Chat {peer_id} was added to the database")
    
    async def close(self):
        logger.debug(f"Disconnecting the database...")
        self._db_client.disconnect()
        logger.debug(f"Database was disconnected")