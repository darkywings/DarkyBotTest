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
        if _type in ["user", "chat"]:
        
            logger.debug(f"Searching records for {_type} with ID {_id}...")
            result = await self._db_client.fetchrow(f"SELECT * FROM {_type}s WHERE {_type}_id = $1", _id)

            if not result:
                logger.debug(f"Record of {_type} with ID {_id} was not found")
                return False
            
            if only_bool:
                return True
            
            logger.debug(f"Record was found: {result}")
            return result
        
        raise ValueError("type arg should be \"user\" or \"chat\"")
    
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
                            _id: int,
                            _title: str,
                            _members: list[dict]):
        '''
        Регистрация чата в базе данных
        Происходит только после вызова определенной команды
        '''
        logger.debug(f"Adding chat {_id} into the database...")
        await self._db_client.execute(
            f"""
            WITH 
                settings AS (INSERT INTO chat_settings DEFAULT VALUES RETURNING id),
                verify AS (INSERT INTO verify_settings DEFAULT VALUES RETURNING id),
                greeting AS (INSERT INTO chat_greetings DEFAULT VALUES RETURNING id),
                rules AS (INSERT INTO chat_rules DEFAULT VALUES RETURNING id)
            INSERT INTO chats (
                chat_id, chat_title, settings_id, verify_settings_id, greeting_id, rules_id
            ) VALUES (
                $1, $2,
                (SELECT id FROM settings),
                (SELECT id FROM verify),
                (SELECT id FROM greeting),
                (SELECT id FROM rules)
            );
            """,
            _id, _title
        )
        await self._db_client.execute(
            f"""
            CREATE TABLE IF NOT EXISTS members_{_id} (
                id SERIAL PRIMARY KEY,
                user_id INT NOT NULL UNIQUE,
                nickname TEXT DEFAULT NULL,
                warns INT DEFAULT 0,
                is_banned BOOLEAN DEFAULT FALSE,
                level INT DEFAULT 0,
                level_xp INT DEFAULT 0,
                messages INT DEFAULT 0,
                bad_words INT DEFAULT 0,
                photo INT DEFAULT 0,
                video INT DEFAULT 0,
                audio INT DEFAULT 0,
                docs INT DEFAULT 0,
                audio_messages INT DEFAULT 0
            );
            """
        )
        await self._db_client.execute(
            f"""
            CREATE TABLE IF NOT EXISTS assocs_{_id} (
                id SERIAL PRIMARY KEY,
                command TEXT NOT NULL UNIQUE,
                assocs TEXT[]
            );
            """
        )
        await self._db_client.execute(
            f"""
            CREATE TABLE IF NOT EXISTS rp_{_id} (
                id SERIAL PRIMARY KEY,
                trigger TEXT NOT NULL UNIQUE,
                f_reply TEXT NOT NULL,
                m_reply TEXT NOT NULL
            );
            """
        )
        await self._db_client.execute(
            f"""
            INSERT INTO rp_{_id} (trigger, f_reply, m_reply) VALUES
            ('буп', '<user1> бупнула <user2> в нос', '<user1> бупнул <user2> в нос'),
            ('кусь', '<user1> укусила <user2>', '<user1> укусил <user2>'),
            ('лизь', '<user1> лизнула <user2>', '<user1> лизнул <user2>'),
            ('обнять', '<user1> обняла <user2>', '<user1> обнял <user2>'),
            ('поцеловать', '<user1> поцеловала <user2>', '<user1> поцеловал <user2>'),
            ('ударить', '<user1> ударила <user2>', '<user1> ударил <user2');
            """
        )
        await self.reg_chat_members(_id, _members)
        logger.debug(f"Chat {_id} was added to the database")
    
    async def reg_chat_members(self, _chat_id, _user_ids):
        '''
        Регистрация нескольких участников в базе данных в таблице участников чата
        '''
        logger.debug(f"Generating query for registering chat members for {_chat_id}...")
        _query = f"INSERT INTO members_{_chat_id} (user_id) VALUES {", ".join([f"({_user_id["member_id"]})" for _user_id in _user_ids if _user_id["member_id"] > 0])};"

        logger.debug(f"Registering members for {_chat_id}...")
        await self._db_client.execute(_query)
        logger.debug(f"Chat members for {_chat_id} was registered")
    
    async def check_registration_chat_member(self,
                                             _chat_id: int,
                                             _user_id: int,
                                             only_bool: bool = True) -> dict | bool:
        logger.debug(f"Searching records for chat member with ID: {_user_id} in chat {_chat_id}...")
        result = await self._db_client.fetchrow(f"SELECT * FROM members_{_chat_id} WHERE user_id = $1", _user_id)

        if not result:
            logger.debug(f"Record with ID {_user_id} was not found in chat {_chat_id}")
            return False
            
        if only_bool:
            return True
            
        logger.debug(f"Record was found: {result}")
        return result
        
    
    async def reg_chat_member(self, _chat_id, _user_id):
        '''
        Регистрация участника в базе данных в таблице участников чата
        '''
        logger.debug(f"Registering chat member {_user_id} in {_chat_id}...")
        await self._db_client.execute(
            f"""
            INSERT INTO members_{_chat_id} (user_id) VALUES ($1);
            """,
            _user_id
        )
        logger.debug(f"Chat member {_user_id} was registered in chat_members")
    
    async def close(self):
        logger.debug(f"Disconnecting the database...")
        await self._db_client.disconnect()
        logger.debug(f"Database was disconnected")