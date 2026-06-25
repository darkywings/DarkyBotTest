from twilight_vk.framework.rules import BaseRule
from twilight_vk.utils.types.event_types import BotEventType

from utils.replies import Replies

class Disabled(BaseRule):

    def __init__(self) -> None:
        '''
        "Отключает" функцию с этим правилом и оповещает об этом пользователя
        '''
        super().__init__(
            on_event_types = [BotEventType.MESSAGE_NEW, BotEventType.MESSAGE_EVENT]
        )

    async def check(self, event: dict):

        _peer_id = event["object"]["message"]["peer_id"] if event.get("type") == BotEventType.MESSAGE_NEW else event["object"]["peer_id"]
        _conversation_message_id = event["object"]["message"]["conversation_message_id"] if event.get("type") == BotEventType.MESSAGE_NEW else event["object"].get("conversation_message_id", None)
        await self.methods.messages.send(peer_id = _peer_id,
                                         forward={
                                             "is_reply": True,
                                             "peer_id": _peer_id,
                                             "conversation_message_ids": _conversation_message_id
                                         },
                                         message = Replies.DISABLED[0],
                                         keyboard = Replies.DISABLED[2])
        return False

class UnderDevelopment(BaseRule):
    
    def __init__(self) -> None:
        '''
        "Отключает" функцию с этим правилом и оповещает о том, что команда в разработке
        '''
        super().__init__(
            on_event_types = [BotEventType.MESSAGE_NEW, BotEventType.MESSAGE_EVENT]
        )

    async def check(self, event: dict):

        _peer_id = event["object"]["message"]["peer_id"] if event.get("type") == BotEventType.MESSAGE_NEW else event["object"]["peer_id"]
        _conversation_message_id = event["object"]["message"]["conversation_message_id"] if event.get("type") == BotEventType.MESSAGE_NEW else event["object"].get("conversation_message_id", None)
        await self.methods.messages.send(peer_id = _peer_id,
                                         forward={
                                             "is_reply": True,
                                             "peer_id": _peer_id,
                                             "conversation_message_ids": _conversation_message_id
                                         },
                                         message = Replies.UNDER_DEVELOPMENT[0],
                                         keyboard = Replies.UNDER_DEVELOPMENT[2])
        return False