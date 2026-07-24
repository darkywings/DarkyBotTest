from typing import TYPE_CHECKING
import re
import random

from twilight_vk.utils.types.response import Response

from utils.random import RandomUtils
from utils.replies import Replies

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
        '''
        Отображение списка установленных РП команд
        '''
        rps = await self._db.all_rp(event["object"]["message"]["peer_id"])
        return (
            "🧾 Список РП-команд в этом чате:\n" \
            f"{"\n".join([f" 🔹 {rp["trigger"].capitalize()}" for rp in rps])}\n" \
            f"❕ Всего РП-команд в этом чате: {len(rps)}\n"
        )

    async def add(self, event: dict, trigger: str, reply_male: str, reply_female: str):
        '''
        Добавление РП команды
        '''
        _chat_id = event["object"]["message"]["peer_id"]

        rps = await self._db.all_rp(_chat_id)
        if trigger in [rp["trigger"] for rp in rps]:
            return "⚠️ Триггер для данной РП-команды уже занят, используйте другой"
        
        if len(rps) >= 50:
            return "❗️ Вы достигли лимита в 50 РП-команд для одного чата. Я не могу добавить новые РП-комады"
        
        await self._db.add_rp(_chat_id, trigger, reply_male, reply_female)
        return f"✅ РП-команда {trigger} была добавлена"

    async def delete(self, event: dict, trigger: str):
        '''
        Удаление РП из базы данных
        '''
        if trigger in ["буп", "кусь", "лизь", "обнять", "ударить", "поцеловать"]:
            return "⚠️ Данную РП-команду нельзя удалить, поскольку она является зарезервированной."
        
        await self._db.remove_rp(chat_id = event["object"]["message"]["peer_id"],
                                 trigger = trigger)
        return f"✅ РП-команда {trigger} была удалена"

    async def edit(self, event: dict, trigger: str, reply_male: str, reply_female: str):
        pass

    async def _prepare_user(self, peer_id: int, user_id: int) -> str:
        '''
        Готовит пользователя для отображения в РП команде (из его ID делает строку вида Имя Фамилия или Никнейм, с упоминанием или без)
        '''
        if user_id < 0:

            _group = await self._methods.groups.getById(group_ids = user_id)
            _group = _group["response"]["groups"][0]

            return f"[club{_group["id"]}|{_group["name"]}]", "male"

        _user = await self._db.get_user(user_id)
        _member = await self._db.get_chat_member(peer_id, user_id)

        if not _user or not _member:
            return False

        _result = _member["nickname"] or f"{_user["first_name"]} {_user["last_name"]}"
        return {
            "who_can_rp": _user["who_can_rp_me"],
            "output": _result if _user["mentions"] == False else f"[id{_user["user_id"]}|{_result}]",
            "sex": _user["sex"]
        }
    
    def _get_output(self, reply: str, user1: str, user2: str) -> str:
        '''
        Подставляет в РП пользователей, если в строке ответа они не обозначены явно - подставляет по краям по умолчанию
        '''
        if "<user1>" not in reply: reply = f"<user1> {reply}"
        if "<user2>" not in reply: reply = f"{reply} <user2>"

        reply = re.sub("<user1>", user1, reply, flags=re.IGNORECASE)
        reply = re.sub("<user2>", user2, reply, flags=re.IGNORECASE)

        return reply

    async def do(self, peer_id: int, from_id: int, rp: str, to_id: int):
        '''
        Идентифицирует РП и формирует ответ в соответствии с настройками
        '''
        rp_reply = await self._db.get_rp_replies(peer_id, rp)

        if not rp_reply:
            return

        user1: dict = await self._prepare_user(peer_id, from_id)
        user2: dict = await self._prepare_user(peer_id, to_id)

        if user2["who_can_rp"] == "only_bot" and from_id > 0:
            return Replies.RP_DENIED_FOR_USERS
        
        if user2["who_can_rp"] == "only_users" and from_id < 0:
            return Replies.RP_DENIED_FOR_BOTS
        
        if user2["who_can_rp"] == "nobody":
            return Replies.RP_DENIED_FOR_ALL

        if not user2:
            return Replies.RP_USER_NOT_FOUND

        return self._get_output(rp_reply["reply_female"] if user1["sex"] == "female" else rp_reply["reply_male"], user1["output"], user2["output"])
    
    async def random_rp(self, event: dict):
        '''
        Вызывает рандомное рп в рандомном чате
        '''
        if random.randint(0, 50) != 0:
            return
        
        _chat_id = event["object"]["message"]["peer_id"]

        rps = await self._db.all_rp(_chat_id)
        members = await self._db.get_members(_chat_id)
        response = await self.do(_chat_id, 
                            -event.get("group_id"), 
                            RandomUtils.choice([rp["trigger"] for rp in rps]), 
                            RandomUtils.choice([user["user_id"] for user in members]))
        if response not in [
            Replies.RP_DENIED_FOR_USERS,
            Replies.RP_DENIED_FOR_BOTS,
            Replies.RP_DENIED_FOR_ALL,
            Replies.RP_USER_NOT_FOUND
        ]:
            return Response(peer_ids=_chat_id, message=response)