from typing import TYPE_CHECKING

from twilight_vk.utils.types.event_types import BotEventType

if TYPE_CHECKING:
    from modules.database import DarkyDatabase
    from modules.assocs import Assoc
    from twilight_vk.framework.methods import VkMethods

class Middleware:

    def __init__(self,
                 db: "DarkyDatabase",
                 methods: "VkMethods",
                 assocs: "Assoc") -> None:
        self._db = db
        self._methods = methods
        self._assocs = assocs
    
    async def prepare_event(self, event: dict) -> dict:

        event.setdefault("user_data", None)
        event.setdefault("chat_data", None)
        event.setdefault("darkybot_admin", None)
        # event.setdefault("is_admin", None)
        # event.setdefault("is_bot_admin", None)

        _from_id: int = None
        _peer_id: int = None

        match event.get("type"):

            case BotEventType.MESSAGE_NEW:

                _from_id = event["object"]["message"]["from_id"]
                _peer_id = event["object"]["message"]["peer_id"]

                event["object"]["message"].setdefault("default_text") = event["object"]["message"]["text"]

                event = await self._assocs.check(event)
            
            case BotEventType.MESSAGE_EVENT:

                _from_id = event["object"]["user_id"]
                _peer_id = event["object"]["peer_id"]
        
        _user_data = await self._db.get_user(_from_id) if _from_id else None
        _chat_data = await self._db.get_chat(_peer_id) if _peer_id else None
        _bot_admin = await self._db.is_bot_admin(_from_id) if _from_id else None

        event["user_data"] = _user_data
        event["chat_data"] = _chat_data
        event["darkybot_admin"] = _bot_admin

        return event