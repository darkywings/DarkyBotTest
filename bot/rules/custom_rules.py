from twilight_vk.framework.rules import BaseRule

class FromChat(BaseRule):
    '''
    Проверка что сообщение пришло из беседы, а не из личных сообщений
    '''

    async def check(self, event: dict):

        if event["object"]["message"]["peer_id"] > 2000000000:
            return True

        return False