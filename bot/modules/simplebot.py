import random

class SimpleCommands:

    async def try_command(msg: str) -> str:
        _results = [
            f"✅Попытка {msg} - оказалась удачной!",
            f"❌Попытка {msg} - оказалась неудачной!"
        ]
        return random.choices(
            population = _results,
            weights = [random.random() for _ in [1] * len(_results)]
        )[0]
    
    async def choice_command(variables: list[str]) -> str:
        return f"🤔Я выбираю {random.choices(
            population = variables,
            weights = [random.random() for _ in [1] * len(variables)]
        )[0]}"

    async def guess_command(msg: str) -> str:
        return f"🔮Вероятность \"{msg}\" составляет {random.randint(0, 100)}%"