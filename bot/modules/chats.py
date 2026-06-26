from typing import TYPE_CHECKING
import logging
import random
import math

from twilight_vk.utils.config import CONFIG as twi_config
from twilight_vk.utils.types.event_types import BotEventType

from utils import bad_words_detector
from utils.rank_renderer import RankCard

if TYPE_CHECKING:
    from twilight_vk.framework.methods import VkMethods
    from modules.database import DarkyDatabase

logger = logging.getLogger("bot-chats")

class Chats:

    def __init__(self,
                 db_client: "DarkyDatabase",
                 methods: "VkMethods"
                 ) -> None:
        self._db = db_client
        self._methods = methods
    
    async def reg_chat(self, event: dict) -> str:
        '''
        Регистрация чата в базе данных
        '''
        _peer_id = event["object"]["message"]["peer_id"] if event["type"] == BotEventType.MESSAGE_NEW else event["object"]["peer_id"]

        if _peer_id < 2000000000:
            logger.error(f"Chat ID cannot be less than 2000000000")
            return

        logger.debug(f"Checking registration for chat {_peer_id}...")
        if await self._db.get_chat(_peer_id):
            logger.debug(f"Chat {_peer_id} is already registered")
            return f"⚠️ Ваш чат уже был ранее зарегистрирован"
        
        logger.debug(f"Registering chat {_peer_id}...")
        _chat = await self._methods.messages.getConversationById(
            peer_ids = _peer_id
        )
        _chat = _chat["response"]["items"][0]

        _chat_members = await self._methods.messages.getConversationMembers(
            peer_id = _peer_id,
            fields = "screen_name, sex"
        )
        _chat_members = _chat_members["response"]["profiles"]

        _chat_id = _chat["peer"]["id"]
        _chat_title = _chat["chat_settings"]["title"]

        for _member in _chat_members:
            await self._db.register_user(_member["id"], 
                                         _member["first_name"],
                                         _member["last_name"],
                                         _member["screen_name"],
                                         "female" if _member["sex"] == 1 else "male")

        await self._db.register_chat(_chat_id, _chat_title, _chat_members)

        logger.info(f"Chat {_peer_id} was registered")
        return f"✅ Ваш чат с ID: {_chat_id} был успешно зарегистрирован"
    
    async def update_timestamp(self, event: dict) -> None:
        '''
        Обновление временной метки чата в базе данных
        '''
        _peer_id = event["object"]["message"]["peer_id"]
        
        logger.debug(f"Updating timestamp for chat {_peer_id}...")
        await self._db.update_chat_timestamp(_peer_id)
        logger.debug(f"Timestamp for chat {_peer_id} updated")
    
    async def reg_chat_member(self, event: dict) -> None:
        '''
        Регистрация участника в чате при каждом новом сообщении
        если до этого он не был зарегистрирован
        '''
        _user_id = event["object"]["message"]["from_id"]
        _peer_id = event["object"]["message"]["peer_id"]

        if _user_id < 0:
            logger.warning(f"{_user_id} is not user")
            return

        logger.debug(f"Checking registration for chat member {_user_id} in {_peer_id}...")
        if await self._db.get_chat_member(_peer_id, _user_id):
            logger.debug(f"Chat member {_user_id} is already registered in chat {_peer_id}")
            return
        
        logger.debug(f"Registering chat_member {_user_id} in chat {_peer_id}...")
        await self._db.reg_chat_member(_peer_id, _user_id)

        logger.info(f"Chat member {_user_id} was registered in chat {_peer_id}")
    
    async def show_chat(self, event: dict) -> str:
        '''
        Отображает данные беседы и ее настройки
        '''
        _peer_id = event["object"]["message"]["peer_id"]

        _chat = await self._db.get_chat(_peer_id)
        logger.info(f"Chat info for {_peer_id} was returned")

        return (
            "🧾 Информация о чате:\n" \
            f" 🔹 ID чата: {_chat["chat_id"]}\n" \
            f" 🔹 ID чата в боте: {_chat["id"]}\n" \
            f" 🔹 Название чата: {_chat["chat_title"]}\n" \
            f" 🔹 Количество РП команд: {_chat["rp_count"]}\n" \
            f" 🔹 Количество зарегистрированных участников: {_chat["members_count"]}\n" \
            f" 🔹 Дата регистрации в боте: {_chat["created_at"]}\n" \
            "⚙️ Настройки чата:\n" \
            f" 🔹 Оповещения бота: {_chat["update_notifications"]}\n" \
            f" 🔹 Упоминания в приветствиях: {_chat["mention_in_greetings"]}\n" \
            f" 🔹 Оповещения о новых уровнях: {_chat["lvlups"]}\n" \
            f" 🔹 РП-команды: {_chat["rp"]}\n" \
            f" 🔹 Никнеймы: {_chat["nicknames"]}\n" \
            f" 🔹 Управление РП-командами: {_chat["manage_rp"]}\n" \
            f" 🔹 Управление никнеймами: {_chat["manage_nicknames"]}\n" \
            f" 🔹 Триггеры: {_chat["triggers"]}\n" \
            f" 🔹 Автоисправление раскладки: {_chat["layout_autodetect"]}\n" \
            f" 🔹 Доступ к запрету сообщений: {_chat["who_can_mute"]}\n" \
            f" 🔹 Доступ к исключению пользователей: {_chat["who_can_kick"]}\n" \
            f" 🔹 Доступ к предупреждениям: {_chat["who_can_warn"]}\n" \
            f" 🔹 Доступ к банам: {_chat["who_can_ban"]}\n" \
            f" 🔹 Лимит предупреждений: {_chat["warn_limit"]}\n" \
            f" 🔹 Наказание за лимит предупреждений: {_chat["warn_punishment"]}\n" \
            f" 🔹 Автокик: {_chat["autokick"]}\n" \
            "🛡 Настройки системы DarkyVerify:\n" \
            f" 🔹 Статус: {_chat["verify_enabled"]}\n" \
            f" 🔹 Наказание: {_chat["verify_punishment"]}\n" \
            f" 🔹 Дней с регистрации должно пройти: {_chat["days_from_signup"]}\n" \
            f" 🔹 Должны быть подписаны на группы: {_chat["should_follow_groups"]}\n" \
            f" 🔹 Спам-защита: {_chat["spam_detection"]}"
            .replace("True", "✅")
            .replace("False", "❌")
            .replace("all", "❕ Все пользователи ❕")
            .replace("nobody", "❌ Никто ❌")
            .replace("admins", "❗️ Только администраторы ❗️")
            .replace("none", "❌ Не установлено ❌")
            .replace("mute", "❕ Запрет на сообщения ❕")
            .replace("kick", "❕ Исключение ❕")
            .replace("ban", "❗️ Бан ❗️")
        )


    async def show_chat_member(self, event: dict, member_id: int):
        '''
        Отображает данные участника беседы
        '''

        # TODO: ЗДЕСЬ ДОЛЖНА БЫТЬ ЕЩЕ КАРТИНКА СТАТИСТИКИ ОТРЕНДЕРЕННАЯ С ГРАФИКОМ АКТИВНОСТИ И ТЕКУЩЕГО УРОВНЯ
        _peer_id = event["object"]["message"]["peer_id"]

        if member_id == -event["group_id"]:
            
            _bot_stats = await self._db.get_bot_stats()
            logger.info(f"Bot info was returned for {_peer_id}")
            return (
                "📊 Статистика Дарки-бота:\n" \
                f" 🔹 Работает и разрабатывается с 9 марта 2020 года.\n" \
                f" 🔹 Версия бота: {_bot_stats["version"]}\n" \
                f" 🔹 Версия фреймворка TWILIGHT: {twi_config.FRAMEWORK.version}\n" \
                f" 🔹 Последнее обновление получено: {_bot_stats["last_update"]}\n" \
                f" 🔹 Создатель бота и фреймворка: {twi_config.FRAMEWORK.developer}\n" \
                f" 🔹 Зарегистрировано бесед: {_bot_stats["chats_total"]}\n" \
                f" 🔹 Зарегистрировано пользователей: {_bot_stats["users_total"]}\n" \
                f" 🔹 Обработано запросов: {_bot_stats["requests_handled"]}"
            )

        if member_id < 0:
            return "⚠️ Я не собираю статистику и не регистрирую других ботов в своей базе, у меня нет необходимости делать это"
        
        _member = await self._db.get_chat_member_stats(_peer_id, member_id)
        _rank_card = await RankCard(await self._db.get_user(member_id),
                                    await self._db.get_activity_stats(_peer_id, member_id)).render()
        _rank_card.save("test.png")
        logger.info(f"Chat member {member_id} info was returned for {_peer_id}")
        return (
            "📊 Статистика участника беседы:\n" \
            f" 🔹 ID пользователя: {_member["user_id"]}\n" \
            f" 🔹 Забанен: {_member["is_banned"]}\n" \
            f" 🔹 Никнейм: {_member["nickname"]}\n" \
            f" 🔹 Место в топе беседы: {_member["top_place"]} / {_member["total_top"]}\n" \
            f" 🔹 Уровень: {_member["level"]}\n" \
            f" 🔹 Опыт: {_member["xp_per_level"]} exp. / {_member["max_xp_per_level"]} exp.\n" \
            f" 🔹 Всего опыта: {_member["level_xp"]}\n" \
            f" 🔹 Предупреждения: {_member["warns"]}\n" \
            f" 🔹 Количество сообщений: {_member["messages"]}\n" \
            f" 🔹 Количество нецензурных слов: {_member["bad_words"]}\n" \
            f" 🔹 Количество отправленных фотографий: {_member["photo"]}\n" \
            f" 🔹 Количество отправленных видео: {_member["video"]}\n" \
            f" 🔹 Количество отправленных аудиозаписей: {_member["audio"]}\n" \
            f" 🔹 Количество отправленных документов: {_member["docs"]}\n" \
            f" 🔹 Количество голосовых сообщений: {_member["audio_messages"]}\n" \
            "[DEV_NOTE]: Здесь должна быть еще картинка с диаграммой активности и отображением прогресс бара для уровня участника \n"
            .replace("True", "✅")
            .replace("False", "❌")
            .replace("None", "❌ Не установлен ❌")
        )
    
    async def update_member_stats(self, event: dict):
        '''
        Обновляет статистику участника беседы
        '''

        if len(list(event["object"]["message"]["text"])) > 500 + random.randint(-50, 50):
            logger.info("Anti-cheat: Too much text at one message")
            return

        _peer_id = event["object"]["message"]["peer_id"]
        _user_id = event["object"]["message"]["from_id"]
        _attachments = event["object"]["message"]["attachments"]
        _text = event["object"]["message"]["text"]

        _xp_count = len(_text)
        _attachments_xps = [0, 0, 0, 0, 0] # photo, video, audio, docs, voice_messages
        _bad_words_count = bad_words_detector.extract_bad_words(_text)["count"]

        if _attachments != []:
            for _attachment in _attachments:
                match _attachment["type"]:
                    case "photo": _attachments_xps[0] += 20
                    case "video": _attachments_xps[1] += 30
                    case "audio": _attachments_xps[2] += 15
                    case "docs": _attachments_xps[3] += 35
                    case "audio_messages": _attachments_xps[4] += 10
        
        _xp_count += sum(_attachments_xps)

        _chat_member = await self._db.get_chat_member_stats(_peer_id, _user_id)
        if not _chat_member:
            logger.warning(f"User {_user_id} not registered yet in chat {_peer_id}")
            return

        _is_lvlups_allowed = await self._db.get_chat(_peer_id)
        _is_lvlups_allowed = _is_lvlups_allowed["lvlups"]

        _level = _chat_member["level"]
        _new_xp = _chat_member["level_xp"] + _xp_count
        _new_level = int((1 + math.sqrt(1 + 4 * _new_xp / 100)) // 2)

        await self._db.update_chat_member_stat(_peer_id, _user_id,
                                               _level = _new_level, _xp = _new_xp,
                                               _messages = _chat_member["messages"] + 1,
                                               _bad_words = _chat_member["bad_words"] + _bad_words_count,
                                               _photo = _attachments_xps[0] / 20,
                                               _video = _attachments_xps[1] / 30,
                                               _audio = _attachments_xps[2] / 15,
                                               _docs = _attachments_xps[3] / 35,
                                               _audio_messages = _attachments_xps[4] / 10)
        
        if (_new_level - _level) > 0:
            logger.info(f"Chat {_peer_id} member {_user_id} got level up! (up to level {_new_level})")

            if _is_lvlups_allowed:

                _user = await self._db.get_user(_user_id)
                _chat = await self._db.get_chat(_peer_id)

                _nickname = _chat_member["nickname"]

                username = _nickname if _nickname is not None and _chat["nicknames"] == True else f"{_user["first_name"]} {_user["last_name"]}"
                achieved = "достигла" if _user["sex"] == "female" else "достиг"

                if _user["mentions"] == True:
                    username = f"[id{_user["user_id"]}|{username}]"

                for lvlup in range(_level, _new_level, 1):
                    await self._methods.messages.send(
                        peer_ids = _peer_id,
                        message = f"🎉 {username} только что {achieved} {lvlup + 1} уровня!"
                    )
            
    async def note_activity(self, event: dict):
        '''
        Запоминает активность участника беседы
        '''
        _peer_id = event["object"]["message"]["peer_id"] if event["type"] == BotEventType.MESSAGE_NEW else event["object"]["peer_id"]
        _user_id = event["object"]["message"]["from_id"] if event["type"] == BotEventType.MESSAGE_NEW else event["object"]["user_id"]

        await self._db.update_activity(_peer_id, _user_id)
    
    async def update_member(self, event: dict, key: str, value: str):
        '''
        Обновляет данные участника беседы
        '''
        pass

    async def update_chat(self, event: dict, key: str, value: str):
        '''
        Обновляет данные чата
        '''
        pass