from twilight_vk.framework.rules import BaseRule

from utils.layout import LayoutChanger

class LayoutRule(BaseRule):

    def __init__(self, need_bool: bool = False) -> None:
        '''
        Определяет является ли выбранная раскладка в тексте корректной, или ее нужно сменить

        :param need_bool: В ответ должна прийти булева переменная или измененный текст
        :type need_bool: bool
        '''
        super().__init__(
            need_bool = need_bool
        )
        self.layout = LayoutChanger()


    async def check(self, event: dict) -> bool:

        _text: str = event["object"]["message"]["text"]

        return await self.layout.detect(_text)
        