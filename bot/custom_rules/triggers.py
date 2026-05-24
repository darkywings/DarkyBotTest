from twilight_vk.framework.rules import BaseRule

class DorkyTrigger(BaseRule):
    '''
    Триггер на "Дурки", "Дорке"
    '''
    async def check(self, event: dict) -> bool:

        for _word in ["дурки", "дорки"]:
            if _word in event["object"]["message"]["text"].lower():
                return True
        return False