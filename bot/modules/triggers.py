from utils.random import RandomUtils

class TriggerReplies:

    def dorky() -> str:

        _results = [
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

        return RandomUtils.choice(_results)