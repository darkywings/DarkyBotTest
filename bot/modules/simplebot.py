import random

from utils.random import RandomUtils
from utils.layout import LayoutChanger

layout = LayoutChanger()

class SimpleCommands:

    def try_command(action: str) -> str:
        '''
        Возвращает случайный исход (удачный/неудачный) для указанной попытки в action

        :param action: Описание действия для которой нужно сделать /roll
        :type action: str
        '''
        _results = [
            f"✅ Попытка {action} - оказалась удачной!",
            f"❌ Попытка {action} - оказалась неудачной!"
        ]
        return RandomUtils.choice(_results)
    
    def choice_command(variables: str) -> str:
        '''
        Возвращает случайно выбранный вариант из предложенных

        :param variables: строка с вариантами выбора через разделитель (или/or)
        :type variables: str
        '''
        for _sep in [" или ", " or "]:
            if _sep in variables:
                variables = variables.split(_sep)
                break
        return f"🤔 Я выбираю {RandomUtils.choice(variables)}"

    def guess_command(user_event: str) -> str:
        '''
        Возвращает случайную вероятность указанного пользователем

        :param user_event: Пользовательское событие
        :type user_event: str 
        '''
        return f"🔮Вероятность \"{user_event}\" составляет {random.randint(0, 100)}%"
    
    def roll(roll_count: int = 1) -> str:
        '''
        Кидает игральную кость в количестве roll_count

        :param roll_count: Количество игральных костей для броска (1-5) (По умолчанию: 1)
        :type roll_count: int
        '''
        if roll_count not in range(1, 6): 
            return "⚠️ Количество кубиков должно быть в диапазоне от 1 до 5 включительно (По умолчанию: 1)"

        rolls = [random.randint(1, 6) for _ in range(0, roll_count, 1)]

        return \
        f"{"\n".join([f"🎲 На кубике {i+1} выпало: {rolls[i]}" for i in range(0, roll_count, 1)])}\n" \
        f"📊 Итого выпало - {sum(rolls)}"
    
    async def layout(text: str) -> str:
        '''
        Сменяет раскладку клавиатуры в тексте

        :param text: Входящий текст
        :type text: bool
        '''
        _correct_text = await layout.detect(text)

        if isinstance(_correct_text, bool) and _correct_text == False:
            return "😥 Я не распознала текст, который можно исправить"
        
        return f"🧐 Текст с исправленной раскладкой: {_correct_text["changed_layout"]}"