from typing import TYPE_CHECKING

from twilight_vk.framework.rules import BaseRule

class FromUser(BaseRule):
    '''
    Проверка что сообщение пришло от пользователя (не бота)
    '''
    async def check(self, event: dict):

        _user_id = event["object"]["message"]["from_id"]

        if _user_id > 0:
            return True
        
        return False

class FromChat(BaseRule):
    '''
    Проверка что сообщение пришло из беседы, а не из личных сообщений
    '''
    async def check(self, event: dict):

        _peer_id = event["object"]["message"]["peer_id"]

        if _peer_id > 2000000000:
            return True
        
        return False