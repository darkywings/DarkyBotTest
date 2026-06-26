from io import BytesIO
from datetime import date, timedelta

from asyncpg import Record

class RankCard:

    def __init__(self,
                 user: dict,
                 data: list[Record]) -> None:
        self._user = user
        self._data = data or []
    
    def _validateData(self):
        '''
        Подготовка данных для отрисовки
        '''
        _today = date.today()

        _activity = {_today - timedelta(days = i): 0 for i in range(13, -1, -1)}

        for _record in self._data:

            _day = _record["date"]
            if _day in _activity:
                _activity[_day] = _record["activity"]
        
        self._data = [
            {"date": _day, "activity": _activity[_day]}
            for _day in sorted(_activity.keys())
        ]

    async def render(self) -> BytesIO:
        self._validateData()
        return self._data