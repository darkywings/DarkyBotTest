from datetime import datetime

from modules.triggers.base import BaseTrigger
from utils.random import RandomUtils

class DorkyTrigger(BaseTrigger):
    '''
    Реакция на дурки/дорки и т.д.
    '''
    def __init__(self) -> None:
        super().__init__(
            _replies = [
                'ДАРКИ!',
                'ДАРКИ Я!', 
                'Я - ДАРКИ!', 
                'Обидно ;с', 
                'Прекратите так меня называть', 
                'Поправочка. Я - Дарки', 
                'Ррр',
                'РРР!',
                'Не называйте меня так'
            ]
        )

class HelloTrigger(BaseTrigger):
    '''
    Реакция на привет и т.д.
    '''
    def __init__(self) -> None:
        super().__init__(
            _replies = [
                "Привет",
                "Приветствую",
                "Рада видеть вас здесь"
            ]
        )
    
class MorningTrigger(BaseTrigger):
    '''
    Реакция на доброе утро
    '''
    def __init__(self) -> None:
        super().__init__(
            _replies = [
                'Утра',
                'Привет',
                'Доброе утро',
                'Доброе',
                'Как спалось?',
                'Надеюсь кошмаров не было',
                'Что снилось?',
                'С пробуждением'
            ]
        )
    
    def react(self):

        _hour = datetime.now().hour

        if _hour > 3 and _hour < 13:
            return RandomUtils.choice(self._replies)

class SleepTrigger(BaseTrigger):
    '''
    Реакция на спокойной ночи
    '''
    def __init__(self) -> None:
        super().__init__(
            _replies = [
                'Спокойной',
                'Спокойной ночи',
                'Споки',
                'Добрых снов',
                'Сладких снов',
                'Спи сладко',
                'Спи крепко',
                'Ночи',
                'Ночки',
                'Приятных снов',
                'Желаю приятных сновидений'
            ]
        )

    def react(self):

        _hour = datetime.now().hour

        if (_hour <= 3) or (_hour > 17 and _hour < 24):
            return RandomUtils.choice(self._replies)