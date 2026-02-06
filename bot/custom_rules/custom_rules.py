from twilight_vk.framework.rules import BaseRule

class FromChat(BaseRule):
    '''
    Проверка что сообщение пришло из беседы, а не из личных сообщений
    '''
    async def check(self, event: dict):

        if event["object"]["message"]["peer_id"] > 2000000000:
            return True

        _peer_id = 0
        _conversation_message_id = 0
        await self.methods.messages.send(peer_id = _peer_id,
                                         forward={
                                             "is_reply": True,
                                             "peer_id": _peer_id,
                                             "conversation_message_id": _conversation_message_id
                                         },
                                         message = "⚠️ Эта команда здесь не работает")
        return False

class Disabled(BaseRule):
    '''
    "Отключает" функцию с этим правилом
    '''
    async def check(self, event: dict):

        _peer_id = 0
        _conversation_message_id = 0
        await self.methods.messages.send(peer_id = _peer_id,
                                         forward={
                                             "is_reply": True,
                                             "peer_id": _peer_id,
                                             "conversation_message_id": _conversation_message_id
                                         },
                                         message = "❌ Данная команда была выключена разработчиком")
        return False