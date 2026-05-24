import random

class Triggers:

    async def dorky() -> str:

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

        return random.choices(
            population = _results,
            weights = [random.random() for _ in [1] * len(_results)]
        )[0]