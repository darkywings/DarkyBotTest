from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from twilight_vk.framework.methods import VkMethods
    from modules.database import DarkyDatabase

class Rp:

    def __init__(self,
                 db: "DarkyDatabase",
                 methods: "VkMethods") -> None:
        '''
        Система РП
        '''
        self._db = db
        self._methods = methods

    async def show(self, event: dict, page: int):
        pass

    async def add(self, event: dict, trigger: str, reply_male: str, reply_female: str):
        pass

    async def delete(self, event: dict, trigger: str):
        pass

    async def edit(self, event: dict, trigger: str, reply_male: str, reply_female: str):
        pass

    async def _prepare_user(self, peer_id: int, user_id: int) -> str:
        '''
        Готовит пользователя для отображения в РП команде (из его ID делает строку вида Имя Фамилия или Никнейм, с упоминанием или без)
        '''
        _user = await self._db.get_user(user_id)
        _member = await self._db.get_chat_member(peer_id, user_id)

        if not _user or not _member:
            return False

        _result = _member["nickname"] or f"{_user["first_name"]} {_user["last_name"]}"
        return _result if _user["mentions"] == False else f"[id{_user["user_id"]}|{_result}]"
    
    async def _get_output(self, reply: str, user1: str, user2: str) -> str:
        '''
        Подставляет в РП пользователей, если в строке ответа они не обозначены явно - подставляет по краям по умолчанию
        '''
        if "<user1>" not in reply: reply = f"<user1> {reply}"
        if "<user2>" not in reply: reply = f"{reply} <user2>"

        re.sub("<user1>", user1, reply, flags=re.IGNORECASE)
        re.sub("<user2>", user2, reply, flags=re.IGNORECASE)

        return reply

    async def do(self, peer_id: int, from_id: int, rp: str, to_id: int):
        '''
        Идентифицирует РП и формирует ответ в соответствии с настройками
        '''
        rp_reply = await self._db.get_rp_replies(peer_id, rp)

        if not rp_reply:
            return

        user1 = await self._prepare_user(peer_id, from_id)
        user2 = await self._prepare_user(peer_id, to_id)

        if not user2:
            return "⚠️ Я не смогла найти данного пользователя в этом чате, вероятно он ни разу не состоял в этой беседе или не активил"

        return self._get_output(rp_reply, user1, user2)