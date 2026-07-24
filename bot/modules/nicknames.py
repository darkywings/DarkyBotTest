from typing import TYPE_CHECKING

from utils.replies import Replies

if TYPE_CHECKING:
    from twilight_vk.framework.methods import VkMethods
    from modules.database import DarkyDatabase

class Nicknames:

    def __init__(self,
                 db: "DarkyDatabase") -> None:
        '''
        Система РП
        '''
        self._db = db
    
    async def set(self,
                  event: dict,
                  user_id: int,
                  nickname: str):
        '''
        Устанавливает никнейм для определенного пользователя

        :param user_id: Идентификатор пользователя которому необходимо установит никнейм (по умолчанию используется from_id из event)
        :type user_id: int
        '''
        if len(nickname.strip()) > 25:
            return Replies.NICKNAME_TOO_LONG
        
        if nickname.startswith("[id"):
            nickname = nickname.rstrip(']').split('|')[-1]
        
        _chat_id = event["object"]["message"]["peer_id"]
        _member_id = user_id
        if _member_id is None:
            _member_id = event["object"]["message"]["from_id"]

        _user = await self._db.get_user(_member_id)
        _member = await self._db.get_chat_member(_chat_id, _member_id)
        if not _user or not _member:
            return Replies.USER_NOT_FOUND

        _username = f"{_user["first_name"]} {_user["last_name"]}"
        _nicknames = await self._db.get_nicknames(_chat_id)

        for _invalid_char in ["[", "]", "$", "|"]:
            if _invalid_char in nickname:
                return Replies.NICKNAME_INVALID_CHARS
        
        if _nicknames and nickname in [_nick["nickname"] for _nick in _nicknames]:
            return Replies.NICKNAME_TAKEN
        
        await self._db.set_nickname(_chat_id, _member_id, nickname)
        return f"✅ Никнейм \"{nickname}\" успешно привязан к пользователю {f"[id{_user["user_id"]}|{_username}]" if _user["mentions"] else _username}"

    async def delete(self,
                     event: dict,
                     user_id: int):
        '''
        Удаляет никнейм для определенного пользователя
        '''
        _chat_id = event["object"]["message"]["peer_id"]
        _member_id = user_id
        if _member_id is None:
            _member_id = event["object"]["message"]["from_id"]

        _user = await self._db.get_user(_member_id)
        _username = f"{_user["first_name"]} {_user["last_name"]}"

        await self._db.remove_nickname(_chat_id, _member_id)
        return f"❗️ Никнейм пользователя {f"[id{_user["user_id"]}|{_username}]" if _user["mentions"] else _username} был сброшен"