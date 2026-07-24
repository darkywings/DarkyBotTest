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
                            _screen_name: str,
                            _sex: str) -> None:
        await self._db_client.execute(
            f"""
            INSERT INTO users (user_id, first_name, last_name, screen_name, sex) VALUES
            ($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING;
            """,
            _id, _first_name, _last_name, _screen_name, _sex
        )
    
    async def register_chat(self,
                            _id: int,
                            _title: str,
                            _members: list[dict]) -> None:
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
            INSERT INTO rp (chat_id, trigger, reply_female, reply_male)
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
                ('ударить', '<user1> ударила <user2>', '<user1> ударил <user2')
            ) AS r(trigger, reply_male, reply_female);
            """,
            _id
        )
        await self.reg_chat_members(_id, _members)
    
    async def reg_chat_members(self,
                               _chat_id: int,
                               _users: list[dict]) -> None:
        _query = f"""
        WITH
            cht AS (SELECT id FROM chats WHERE chat_id = $1), 
            usr AS (SELECT id FROM users WHERE user_id = ANY($2::int[])) 
        INSERT INTO chat_members (chat_id, user_id) 
        SELECT cht.id, usr.id 
        FROM cht, usr;
        """
        await self._db_client.execute(_query, _chat_id, [_user["id"] for _user in _users])
    
    async def get_chat_member(self,
                              _chat_id: int,
                              _user_id: int) -> dict | bool:
        result = await self._db_client.fetchrow("SELECT * FROM chat_members " \
                                                "WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) " \
                                                "AND user_id = (SELECT id FROM users WHERE user_id = $2)",
                                                _chat_id, _user_id)
        return result if result else False
        
    async def reg_chat_member(self, 
                              _chat_id: int,
                              _user_id: int) -> None:
        await self.reg_chat_members(_chat_id, [_user_id])
    
    async def update_chat_timestamp(self,
                                    _chat_id: int) -> None:
        await self._db_client.execute(
            f"""
            UPDATE chats
            SET updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = $1;
            """,
            _chat_id
        )

    async def update_user_timestamp(self,
                                    _user_id: int) -> None:
        await self._db_client.execute(
            f"""
            UPDATE users
            SET updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $1;
            """,
            _user_id
        )
    
    async def is_bot_admin(self,
                           _user_id: int) -> bool:
        result = await self._db_client.fetchrow(f"SELECT * FROM admins WHERE user_id = $1", _user_id)
        return True if result else False
    
    async def get_user(self,
                       _user_id: int) -> "Record":
        result = await self._db_client.fetchrow(f"SELECT * FROM users WHERE user_id = $1", _user_id)
        return result if result else False
    
    async def update_user(self,
                          _user_id: int,
                          _key: str,
                          _value: str) -> None:
        await self._db_client.execute(f"UPDATE users SET {_key} = $2 WHERE user_id = $1", _user_id, _value)

    async def get_chat(self,
                       _chat_id: int) -> "Record":
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
            "   settings.random_rp, " \
            "   settings.random_messages, " \
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
            "   verify_settings.join_check, " \
            "   verify_settings.groups_to_follow, "
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
        return _chat if _chat else False
    
    async def update_chat_settings(self,
                                   _chat_id: int,
                                   _key: str,
                                   _value: str) -> None:
        await self._db_client.execute(f"UPDATE chat_settings SET {_key} = $2 WHERE id = (SELECT verify_settings_id FROM chats WHERE chat_id = $1)", _chat_id, _value)
        
    async def update_verify_settings(self,
                                     _chat_id: int,
                                     _key: str,
                                     _value: str) -> None:
        await self._db_client.execute(f"UPDATE verify_settings SET {_key} = $2 WHERE id = (SELECT settings_id FROM chats WHERE chat_id = $1)", _chat_id, _value)
        
    async def get_chat_member_stats(self,
                                    _chat_id: int,
                                    _member_id: int) -> "Record":
        result = await self._db_client.fetchrow(
            """
            SELECT 
                member.id, u.user_id, u.first_name, u.last_name, u.screen_name, 
                member.nickname, 
                member.warns, member.is_banned, member.is_left, 
                (SELECT COUNT(*) + 1 FROM chat_members WHERE chat_id = c.id 
                AND (level_xp > member.level_xp OR (level_xp = member.level_xp AND user_id < member.user_id)) 
                AND is_banned = FALSE AND is_left = FALSE) AS top_place, 
                (SELECT COUNT(*) FROM chat_members WHERE chat_id = c.id AND is_banned = FALSE AND is_left = FALSE) AS total_top, 
                member.level, member.level_xp, 
                (member.level_xp - (100 * member.level * (member.level - 1))) AS xp_per_level, 
                (200 * member.level) AS max_xp_per_level, 
                member.messages, member.bad_words, 
                member.photo, member.video, member.audio, member.docs, member.audio_messages 
            FROM chat_members member 
            JOIN users u ON member.user_id = u.id
            JOIN chats c ON member.chat_id = c.id
            WHERE c.chat_id = $1 AND u.user_id = $2
            """,
            _chat_id, _member_id
        )
        return result if result else False
    
    async def get_bot_stats(self) -> "Record":
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
        return _result
    
    async def add_request_handled(self) -> None:
        await self._db_client.execute(f"UPDATE settings SET requests_handled = requests_handled + 1;")
    
    async def update_chat_member_stat(self,
                                      _chat_id: int, _user_id: int,
                                      _level: int, _xp: int,
                                      _messages: int, _bad_words: int,
                                      _photo: int, _video: int, _audio: int, _docs: int, _audio_messages: int) -> None:
        await self._db_client.execute(
            f"""
            UPDATE chat_members 
            SET 
                level = $3, 
                level_xp = $4, 
                messages = $5, 
                bad_words = $6, 
                photo = $7, 
                video = $8, 
                audio = $9, 
                docs = $10, 
                audio_messages = $11 
            WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) 
            AND user_id = (SELECT id FROM users WHERE user_id = $2);
            """,
            _chat_id, _user_id,
            _level, _xp, _messages, _bad_words,
            _photo, _video, _audio, _docs, _audio_messages
        )
    
    async def update_activity(self,
                              _chat_id: int,
                              _user_id: int) -> None:
        await self._db_client.execute(
            "WITH " \
            "   cht AS (SELECT id FROM chats WHERE chat_id = $1), " \
            "   usr AS (SELECT id FROM users WHERE user_id = $2) " \
            "INSERT INTO member_activity (chat_id, user_id, date, activity) " \
            "SELECT cht.id, usr.id, CURRENT_DATE, 1 " \
            "FROM cht, usr " \
            "ON CONFLICT (chat_id, user_id, date) " \
            "DO UPDATE SET activity = member_activity.activity + 1",
            _chat_id, _user_id
        )
    
    async def get_activity_stats(self,
                                 chat_id: int,
                                 user_id: int) -> "list[Record]":
        _records = await self._db_client.fetch(
            "SELECT date, activity " \
            "FROM member_activity " \
            "WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) " \
            "AND user_id = (SELECT id FROM users WHERE user_id = $2) " \
            "ORDER BY date DESC " \
            "LIMIT 14",
            chat_id, user_id
        )
        return _records
    
    async def add_assoc(self,
                        chat_id: int,
                        command: str,
                        assoc: str) -> None:
        await self._db_client.execute(
            "WITH " \
            "    chat AS (SELECT id FROM chats WHERE chat_id = $1) " \
            "INSERT INTO chat_assocs (chat_id, command, assocs) " \
            "SELECT id, $2, ARRAY[$3] " \
            "FROM chat " \
            "ON CONFLICT (chat_id, command) DO " \
            "UPDATE SET assocs = array_append(chat_assocs.assocs, $3) " \
            "WHERE $3 <> ALL(chat_assocs.assocs);",
            chat_id, command, assoc
        )

    async def delete_assoc(self,
                           chat_id: int,
                           assoc: str) -> None:
        await self._db_client.execute(
            "WITH " \
            "   chat AS (SELECT id FROM chats WHERE chat_id = $1) " \
            "UPDATE chat_assocs SET assocs = array_remove(assocs, $3) " \
            "FROM chat " \
            "WHERE chat_assocs.chat_id = chat.id",
            chat_id, assoc
        )

    async def get_assocs(self,
                         chat_id: int) -> "Record":
        _assocs = await self._db_client.fetch(
            "SELECT command, assocs FROM chat_assocs WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1)", chat_id
        )
        return _assocs if _assocs else False
    
    async def get_nicknames(self,
                            chat_id: int) -> "Record":
        _nicknames = await self._db_client.fetch(
            "SELECT u.user_id, nickname FROM chat_members " \
            "JOIN users u ON chat_members.user_id = u.id " \
            "WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) " \
            "AND nickname IS NOT NULL;", chat_id
        )
        return _nicknames if _nicknames else False
    
    async def get_rp_replies(self,
                             chat_id: int,
                             rp: str) -> "Record":
        _rp = await self._db_client.fetchrow(
            "SELECT reply_male, reply_female FROM rp " \
            "WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) " \
            "AND trigger = $2;",
            chat_id, rp
        )
        return _rp if _rp else False
    
    async def add_rp(self,
                     chat_id: int,
                     trigger: str,
                     reply_male: str,
                     reply_female: str) -> None:
        await self._db_client.execute(
            "WITH " \
            "   chat AS (SELECT id FROM chats WHERE chat_id = $1) " \
            "INSERT INTO rp (chat_id, trigger, reply_male, reply_female) " \
            "SELECT" \
            "   chat.id, " \
            "   new_rp.trigger, " \
            "   new_rp.reply_male, " \
            "   new_rp.reply_female " \
            "FROM chat " \
            "CROSS JOIN (VALUES " \
            "   ($2, $3, $4)" \
            ") as new_rp (trigger, reply_male, reply_female) " \
            "ON CONFLICT (chat_id, trigger) DO " \
            "NOTHING;",
            chat_id, trigger, reply_male, reply_female
        )
    
    async def remove_rp(self,
                        chat_id: int,
                        trigger: str) -> None:
        await self._db_client.execute(
            "DELETE FROM rp " \
            "WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) " \
            "AND trigger = $2;",
            chat_id, trigger
        )
    
    async def all_rp(self,
                     chat_id: int) -> "Record":
        _rps = await self._db_client.fetch(
            "SELECT trigger FROM rp " \
            "WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1)",
            chat_id
        )
        return _rps if _rps else False
    
    async def set_nickname(self,
                           chat_id: int,
                           member_id: int,
                           nickname: str) -> None:
        await self._db_client.execute(
            "UPDATE chat_members " \
            "SET nickname = $3 " \
            "WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) " \
            "AND user_id = (SELECT id FROM users WHERE user_id = $2);",
            chat_id, member_id, nickname
        )

    async def remove_nickname(self,
                              chat_id: int,
                              member_id: int) -> None:
        await self._db_client.execute(
            "UPDATE chat_members " \
            "SET nickname = NULL " \
            "WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) " \
            "AND user_id = (SELECT id FROM users WHERE user_id = $2)",
            chat_id, member_id
        )
    
    async def get_members(self,
                          chat_id: int) -> "Record":
        members = await self._db_client.fetch(
            "SELECT " \
            "   u.user_id " \
            "FROM chat_members m " \
            "JOIN users u ON u.id = m.user_id " \
            "WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) " \
            "AND m.is_banned = FALSE " \
            "AND m.is_left = FALSE",
            chat_id
        )
        return members if members else False

    async def get_top_members(self,
                              chat_id: int,
                              limit: int = 5) -> "Record":
        top_members = await self._db_client.fetch(
            "SELECT " \
            "   u.user_id, " \
            "   u.first_name, " \
            "   u.last_name, " \
            "   m.nickname, " \
            "   m.level_xp, " \
            "   ROW_NUMBER() OVER (ORDER BY m.level_xp DESC) AS position " \
            "FROM chat_members m " \
            "JOIN users u ON u.id = m.user_id " \
            "WHERE chat_id = (SELECT id FROM chats WHERE chat_id = $1) " \
            "AND m.is_banned = FALSE " \
            "AND m.is_left = FALSE " \
            "ORDER BY level_xp DESC " \
            "LIMIT $2",
            chat_id,
            limit
        )
        return top_members if top_members else False