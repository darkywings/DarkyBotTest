import logging
import re
from typing import TYPE_CHECKING

from twilight_vk.utils.types.event_types import BotEventType

if TYPE_CHECKING:
    from asyncpg import Record
    from modules.database import DarkyDatabase

logger = logging.getLogger("bot-assocs")

class Assoc:

    def __init__(self,
                 db: "DarkyDatabase") -> None:
        self._db = db

    async def show_list(self, event: dict, page: int):
        pass

    async def show_assocs(self, event: dict, command: str):
        pass

    async def add(self, event: dict, command: str, assoc: str) -> str:
        '''
        Добавление ассоциации в базу данных чата

        :param command: Команда для которой необходимо добавить ассоциацию
        :type command: str

        :param assoc: Ассоциация для команды command
        :type assoc: str
        '''
        _chat_id = event["object"]["message"]["peer_id"]
        command = command.lower()
        assoc = assoc.lower()

        logger.debug(f"Checking if assoc {assoc} is free to use in chat {_chat_id}...")
        assocs = await self._db.get_assocs(_chat_id)

        if assocs != False:
            for _assoc in assocs:
                _command = _assoc["command"]
                if assoc in _assoc["assocs"]:
                    logger.debug(f"Assoc {assoc} is already in use for command {_command}")
                    return f"⚠️ Ассоциация \"{assoc}\" уже зарезервирована командой \"{_command}\", используйте другую ассоциацию или удалите уже существующую"
        
        logger.debug(f"Assoc {assoc} is free to use in chat {_chat_id}")

        await self._db.add_assoc(_chat_id, command, assoc)
        logger.info(f"Assoc {assoc} was added up for {command} in chat {_chat_id}")
        return f"✅ Ассоциация \"{assoc}\" была успешно привязана к команде \"{command}\""

    async def delete(self, event: dict, assoc: str) -> str:
        '''
        Удаление ассоциации из базы данных чата

        :param assoc: Ассоциация, которую необходимо удалить
        :type assoc: str
        '''
        _chat_id = event["object"]["message"]["peer_id"]
        assoc = assoc.lower()

        logger.debug(f"Checking if assoc {assoc} is existing in chat {_chat_id}...")
        assocs = await self._db.get_assocs(_chat_id)

        if assocs != False:
            for _assoc in assocs:
                if assoc in _assoc["assocs"]:
                    logger.debug(f"Assoc {assoc} was found in command {_assoc["command"]} in chat {_chat_id}")

                    await self._db.delete_assoc(_chat_id, assoc)
                    logger.info(f"Assoc {assoc} was deleted from chat {_chat_id}")
                    return f"✅ Ассоциация \"{assoc}\" была удалена"
            
        logger.debug(f"Assoc {assoc} is not in use in chat {_chat_id}")
        return f"⚠️ Ассоциация \"{assoc}\" не используется в этом чате"

    async def check(self, event: dict) -> str:
        '''
        Поиск оригинальной команды по ассоциации и замена ее в сообщении
        '''

        _chat_id: int = event["object"]["message"]["peer_id"]
        _from_id: int = event["object"]["message"]["from_id"]
        _message: str = event["object"]["message"]["text"]
        _message_low: str = _message.lower()

        logger.debug(f"Checking for assocs in chat {_chat_id}")
        assocs = await self._db.get_assocs(_chat_id)

        #TODO: get nicknames

        if assocs != False:
            
            for assoc in assocs:
                _assocs, _command = assoc["assocs"], assoc["command"]
                for _assoc in _assocs:
                    if _assoc in _message_low:
                        logger.info(f"Assoc {_assoc} was found and was replaced on {_command} in {_chat_id}")
                        _message = re.sub(_assoc, _command, _message, flags = re.IGNORECASE)

            _message = re.sub("myself", f"[id{_from_id}|@id{_from_id}]", _message, flags = re.IGNORECASE)
            
            event["object"]["message"]["text"] = _message
            return event
        
        logger.debug(f"No assocs found for the message {_message}")
        return event