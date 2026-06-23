from twilight_vk.framework.rules import BaseRule

from utils.replies import Replies

class Disabled(BaseRule):
    '''
    "Отключает" функцию с этим правилом и оповещает об этом пользователя
    '''

    async def check(self, event: dict):

        _peer_id = event["object"]["message"]["peer_id"]
        _conversation_message_id = event["object"]["message"]["conversation_message_id"]
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
    '''
    "Отключает" функцию с этим правилом и оповещает о том, что команда в разработке
    '''

    async def check(self, event: dict):

        _peer_id = event["object"]["message"]["peer_id"]
        _conversation_message_id = event["object"]["message"]["conversation_message_id"]
        await self.methods.messages.send(peer_id = _peer_id,
                                         forward={
                                             "is_reply": True,
                                             "peer_id": _peer_id,
                                             "conversation_message_ids": _conversation_message_id
                                         },
                                         message = Replies.UNDER_DEVELOPMENT[0],
                                         keyboard = Replies.UNDER_DEVELOPMENT[2])
        return False