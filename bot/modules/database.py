import os
import logging
from typing import TYPE_CHECKING
from dotenv import load_dotenv

from utils.db_client import AsyncPGClient

if TYPE_CHECKING:
    from asyncpg import Record

logger = logging.getLogger("db-client")

load_dotenv()

class DarkyDatabase:

    def __init__(self):
        logger.debug(f"Connecting to the database...")
        self._db_client: AsyncPGClient = AsyncPGClient(
            dsn = f"postgresql://{os.getenv("POSTGRES_BOT_USER")}:{os.getenv("POSTGRES_BOT_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("POSTGRES_BOT_DB")}"
        )
        logger.debug("Database is connected")

    async def close(self):
        logger.debug(f"Disconnecting the database...")
        await self._db_client.disconnect()
        logger.debug(f"Database was disconnected")
    
    async def register_user(self,
                            _id: int,
                            _first_name: str,
                            _last_name: str,
                            _screen_name: str) -> None:
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
        logger.debug(f"User {_id} was added into the database")
    
    async def register_chat(self,
                            _id: int,
                            _title: str,
                            _members: list[dict]) -> None:
        '''
        Регистрация чата в базе данных
        Происходит только после вызова определенной команды

        :param _id: Идентификатор чата
        :type _id: int

        :param _title: Название чата
        :type _title: str

        :param _members: Список участников чата
        :type _members: list[dict]
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
            WITH
                chat AS (SELECT id FROM chats WHERE chat_id = $1)
            INSERT INTO rp (chat_id, trigger, reply_male, reply_female)
            SELECT 
                chat.id, 
                r.trigger, 
                r.reply_male, 
                r.reply_female
            FROM chat
            CROSS JOIN (VALUES
                ('буп', '<user1> бупнула <user2> в нос', '<user1> бупнул <user2> в нос'),
                ('кусь', '<user1> укусила <user2>', '<user1> укусил <user2>'),
                ('лизь', '<user1> лизнула <user2>', '<user1> лизнул <user2>'),
                ('обнять', '<user1> обняла <user2>', '<user1> обнял <user2>'),
                ('поцеловать', '<user1> поцеловала <user2>', '<user1> поцеловал <user2>'),
                ('ударить', '<user1> ударила <user2>', '<user1> ударил <user2');
            ) AS r(trigger, reply_male, reply_female);
            """,
            _id
        )
        await self.reg_chat_members(_id, _members)
        logger.debug(f"Chat {_id} was added to the database")
    
    async def reg_chat_members(self,
                               _chat_id: int,
                               _users: list[dict]) -> None:
        '''
        Регистрация нескольких участников в таблице участников чата

        :param _chat_id: Идентификатор чата в котором надо зарегистрировать участников
        :type _chat_id: int

        :param _users: Список словарей участников для регистрации в чате
        :type _users: list[dict]
        '''
        logger.debug(f"Generating query for registering chat members for {_chat_id}...")
        _query = f"""
        WITH
            chat AS (SELECT id FROM chats WHERE chat_id = $1)
        INSERT INTO chat_members (chat_id, user_id) 
        SELECT 
            chat.id, 
            user.id
        CROSS JOIN (VALUES
            {", ".join([f"({_user["id"]})" for _user in _users])}
        ) AS user(user_id);
        """

        logger.debug(f"Registering members for {_chat_id}...")
        await self._db_client.execute(_query, _chat_id)
        logger.debug(f"Chat members for {_chat_id} was registered")
    
    async def get_chat_member(self,
                              _chat_id: int,
                              _user_id: int) -> dict | bool:
        '''
        Получить участника чата

        :param _chat_id: Идентификатор чата в котором надо получить участника
        :type _chat_id: int

        :param _user_id: Идентификатор участника
        :type _user_id: int
        '''
        logger.debug(f"Searching records for chat member with ID: {_user_id} in chat {_chat_id}...")
        result = await self._db_client.fetchrow(f"SELECT * FROM chat_members WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) AND user_id = $2",
                                                _chat_id, _user_id)

        if not result:
            logger.debug(f"Record with ID {_user_id} was not found in chat {_chat_id}")
            return False
            
        logger.debug(f"Record was found: {result}")
        return result
        
    async def reg_chat_member(self, 
                              _chat_id: int,
                              _user_id: int) -> None:
        '''
        Регистрация одного участника в таблице участников чата

        :param _chat_id: Идентификатор чата в котором надо зарегистрировать участников
        :type _chat_id: int

        :param _user_id: Идентификатор участника
        :type _user_id: int
        '''
        logger.debug(f"Registering chat member {_user_id} in {_chat_id}...")
        await self.reg_chat_members(_chat_id, [_user_id])
        logger.debug(f"Chat member {_user_id} was registered in chat_members {_chat_id}")
    
    async def update_chat_timestamp(self,
                                    _chat_id: int) -> None:
        '''
        Обновление временной метки чата в базе данных

        :param _chat_id: Идентификатор чата в котором необходимо обновить временную метку
        :type _chat_id: int
        '''
        logger.debug(f"Updating timestamp for {_chat_id}...")
        await self._db_client.execute(
            f"""
            UPDATE chats
            SET updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = $1;
            """,
            _chat_id
        )
        logger.debug(f"Timestamp for {_chat_id} updated")

    async def update_user_timestamp(self,
                                    _user_id: int) -> None:
        '''
        Обновление временной метки чата в базе данных

        :param _user_id: Идентификатор чата в котором необходимо обновить временную метку
        :type _user_id: int
        '''
        logger.debug(f"Updating timestamp for {_user_id}...")
        await self._db_client.execute(
            f"""
            UPDATE users
            SET updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $1;
            """,
            _user_id
        )
        logger.debug(f"Timestamp for {_user_id} updated")
    
    async def is_bot_admin(self,
                           _user_id: int) -> bool:
        '''
        Проверка что пользователь является администратором бота

        :param _user_id: Идентификатор пользователя для проверки
        :type _user_id: int
        '''
        logger.debug(f"Searching records for admins with ID {_user_id}...")
        result = await self._db_client.fetchrow(f"SELECT * FROM admins WHERE user_id = $1", _user_id)

        if not result:
            logger.debug(f"Record of admins with ID {_user_id} was not found")
            return False
        
        return True
    
    async def get_user(self,
                       _user_id: int) -> "Record":
        '''
        Проверка регистрации пользователя

        :param _user_id: Идентификатор пользователя для проверки
        :type _user_id: int
        '''
        logger.debug(f"Searching user {_user_id}...")
        result = await self._db_client.fetchrow(f"SELECT * FROM users WHERE user_id = $1", _user_id)

        if not result:
            logger.debug(f"Record of user {_user_id} was not found")
            return False
        
        return result
    
    async def update_user(self,
                          _user_id: int,
                          _key: str,
                          _value: str) -> None:
        '''
        Обновление полей пользователя в таблцие

        :param _user_id: Идентификатор пользователя для изменения данных
        :type _user_id: int

        :param _key: Название параметра (столбца) для изменения
        :type _key: str

        :param _value: Новое значение параметра _key
        :type _value: str
        '''
        logger.debug(f"Updating user {_user_id}...")
        await self._db_client.execute(f"UPDATE users SET {_key} = $2 WHERE user_id = $1", _user_id, _value)
        logger.debug(f"User {_user_id} is updated")
    
    async def get_chat(self,
                       _chat_id: int) -> "Record":
        '''
        Проверка регистрации чата и возврат всех его данных одной записью

        :param _chat_id: Идентификатор чата для проверки
        :type _chat_id: int
        '''
        logger.debug(f"Searching chat {_chat_id}...")
        _chat = await self._db_client.fetchrow(
            "SELECT " \
            "   chat.id, chat.chat_id, chat.chat_title, chat.created_at, chat.updated_at," \
            "   settings.update_notifications, " \
            "   settings.mention_in_greetings, " \
            "   settings.lvlups, " \
            "   settings.rp, " \
            "   settings.nicknames, " \
            "   settings.manage_rp, " \
            "   settings.manage_nicknames, " \
            "   settings.triggers, " \
            "   settings.layout_autodetect, " \
            "   settings.who_can_mute, " \
            "   settings.who_can_kick, " \
            "   settings.who_can_warn, " \
            "   settings.who_can_ban, " \
            "   settings.warn_limit, " \
            "   settings.warn_punishment, " \
            "   settings.autokick, " \
            "   verify_settings.enabled AS verify_enabled, " \
            "   verify_settings.punishment AS verify_punishment, " \
            "   verify_settings.days_from_signup, " \
            "   verify_settings.should_follow_groups, " \
            "   verify_settings.spam_detection, " \
            "   (SELECT COUNT(*) FROM rp WHERE chat_id = chat.id) AS rp_count, " \
            "   (SELECT COUNT(*) FROM chat_members WHERE chat_id = chat.id) AS members_count " \
            "FROM chats chat " \
            "JOIN chat_settings settings ON chat.settings_id = settings.id " \
            "JOIN verify_settings ON chat.verify_settings_id = verify_settings.id "
            "WHERE chat.chat_id = $1",
            _chat_id
        )

        if not _chat:
            logger.debug(f"Record of chat {_chat} was not found")
            return False
        
        return _chat
    
    async def update_chat_settings(self,
                                   _chat_id: int,
                                   _key: str,
                                   _value: str) -> None:
        '''
        Обновление полей чата в таблице

        :param _chat_id: Идентификатор чата для изменения данных
        :type _chat_id: int

        :param _key: Название параметра (столбца) для изменения
        :type _key: str

        :param _value: Новое значение параметра _key
        :type _value: str
        '''
        pass

    async def update_verify_settings(self,
                                     _chat_id: int,
                                     _key: str,
                                     _value: str) -> None:
        '''
        Обновление полей чата в системе DarkyVerify в таблице

        :param _chat_id: Идентификатор чата для изменения данных
        :type _chat_id: int

        :param _key: Название параметра (столбца) для изменения
        :type _key: str

        :param _value: Новое значение параметра _key
        :type _value: str
        '''
        pass

    async def get_chat_member_stats(self,
                                    _chat_id: int,
                                    _member_id: int) -> "Record":
        '''
        Получить участника чата для вывода статистики

        :param _chat_id: Идентификатор чата в котором надо зарегистрировать участников
        :type _chat_id: int

        :param _member_id: Идентификатор участника
        :type _member_id: int
        '''
        logger.debug(f"Searching records for chat member with ID: {_member_id} in chat {_chat_id}...")
        result = await self._db_client.fetchrow(
            """
            SELECT 
                member.id, member.user_id, 
                member.nickname, 
                member.warns, member.is_banned, 
                (ROW_NUMBER() OVER (ORDER BY member.level_xp DESC)) AS top_place, 
                (SELECT COUNT(*) FROM members WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1)) AS total_top, 
                member.level, member.level_xp, 
                (member.level_xp - (200 * (member.level - 1))) AS xp_per_level, 
                (200 * member.level) AS max_xp_per_level, 
                member.messages, member.bad_words, 
                member.photo, member.video, member.audio, member.docs, member.audio_messages 
            FROM chat_members member 
            WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) 
                AND user_id = $2
            """,
            _chat_id, _member_id
        )

        if not result:
            logger.debug(f"Record with ID {_member_id} was not found in chat {_chat_id}")
            return False
            
        logger.debug(f"Record was found: {result}")
        return result
    
    async def get_bot_stats(self) -> "Record":
        '''
        Получить статистику бота
        '''
        logger.debug(f"Getting bot settings...")
        _result = await self._db_client.fetchrow(
            """
            SELECT 
                bot_info.version, 
                bot_info.last_update, 
                bot_info.requests_handled, 
                (SELECT COUNT(*) FROM chats) AS chats_total, 
                (SELECT COUNT(*) FROM users) AS users_total 
            FROM settings bot_info
            LIMIT 1;
            """
        )
        logger.debug(f"Bot settings was got")
        return _result