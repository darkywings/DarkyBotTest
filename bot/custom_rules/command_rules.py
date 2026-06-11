from twilight_vk.framework.rules import BaseRule

class FromChat(BaseRule):
    '''
    Проверка что сообщение пришло из беседы, а не из личных сообщений
    '''
    async def check(self, event: dict):

        _peer_id = event["object"]["message"]["peer_id"]

        if _peer_id > 2000000000:
            return True
        
        _conversation_message_id = event["object"]["message"]["conversation_message_id"]
        await self.methods.messages.send(peer_id = _peer_id,
                                         forward={
                                             "is_reply": True,
                                             "peer_id": _peer_id,
                                             "conversation_message_ids": _conversation_message_id
                                         },
                                         message = "⚠️ Эта команда здесь не работает")
        return False

class Disabled(BaseRule):
    '''
    "Отключает" функцию с этим правилом
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
                                         message = "❌ Данная команда была выключена разработчиком")
        return False