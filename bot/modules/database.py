import os
import logging
from dotenv import load_dotenv

from utils.db_client import AsyncPGClient

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
                                 _type: str,
                                 _id: int,
                                 only_bool: bool = True) -> dict | bool:
        '''
        Проверка регистрации пользователя или чата в базе данных
        Возвращает найденный объект при наличии иначе False

        :param _type: тип объекта (user/chat)
        :type _type: str

        :param _id: идентификатор объекта
        :type _id: int

        :param only_bool: возврат только булева переменной, или найденного объекта
        :type only_bool: bool
        '''
        if _type not in ["user", "chat"]:
            raise ValueError("type arg should be \"user\" or \"chat\"")
        
        logger.debug(f"Searching records for {_type} with ID {_id}...")
        result: dict = await self._db_client.fetchrow(f"SELECT * FROM {_type}s WHERE {_type}_id = $1", _id)

        if not result:
            logger.debug(f"Record of {_type} with ID {_id} was not found")
            return False
        
        if only_bool:
            return True
        
        logger.debug(f"Record was found: {result}")
        return result
    
    async def register_user(self,
                            _id: int,
                            _first_name: str,
                            _last_name: str,
                            _screen_name: str):
        '''
        Регистрация пользователя в базе данных
        Происходит автоматически при каждом новом сообщении от этого пользователя

        :param _id: идентификатор пользователя в ВК
        :type _id: int

        :param _first_name: имя пользователя в ВК
        :type _first_name: str

        :param _last_name: фамилия пользователя в ВК
        :type _last_name: str

        :param _screen_name: короткое имя пользователя в ВК
        :type _screen_name
        '''
        logger.debug(f"Adding user {_id} into the database...")
        await self._db_client.execute(
            f"""
            INSERT INTO users (user_id, first_name, last_name, screen_name) VALUES
            ($1, $2, $3, $4);
            """,
            _id, _first_name, _last_name, _screen_name
        )
        await self._db_client.execute(
            f"""
            CREATE TABLE IF NOT EXISTS notes_{_id} (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            );
            """
        )
        logger.debug(f"User {_id} was added into the database")
    
    async def register_chat(self,
                            peer_id: int,
                            title: str):
        '''
        Регистрация чата в базе данных
        Происходит только после вызова определенной команды
        '''
        pass
    
    async def close(self):
        logger.debug(f"Disconnecting the database...")
        await self._db_client.disconnect()
        logger.debug(f"Database was disconnected")