import re
import math
from collections import Counter

class LayoutChanger:

    def __init__(self) -> None:
        '''
        Класс для автоматического определения и изменения раскладки сообщения
        '''
        self.RU_BIGRAM = {
            'ст', 'но', 'то', 'на', 'ен', 'ов', 'ко', 'ра', 'по', 'ал', 'ро', 'во', 'ол', 'ла', 'не',
            'го', 'ре', 'те', 'пр', 'ан', 'ли', 'ни', 'ис', 'от', 'ве', 'ти', 'ом', 'тр', 'се', 'ме',
            'де', 'ка', 'ос', 'ит', 'ть', 'ел', 'ва', 'со', 'од', 'ир', 'ак', 'тр', 'ьн', 'ск', 'ки',
            'ин', 'то', 'то', 'на', 'ит'
        }
        self.EN_BIGRAM = {
            'th', 'he', 'in', 'er', 'an', 're', 'nd', 'at', 'on', 'nt', 'ha', 'es', 'st', 'en', 'ed',
            'to', 'it', 'ou', 'ea', 'hi', 'is', 'or', 'ti', 'as', 'te', 'et', 'ng', 'of', 'al', 'de',
            'se', 'le', 'sa', 'si', 'ar', 've', 'ra', 'ld', 'ur', 'ro', 'pe', 'ne', 'me', 'll', 'co',
            'ta', 'di', 'la', 'li', 'io'
        }
        self.LAYOUT = {
            'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з',
            '[': 'х', ']': 'ъ', 'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л', 'l': 'д',
            ';': 'ж', "'": 'э', 'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь', ',': 'б', '.': 'ю',
            '`': 'ё'
        }
        self.FREQ_RU = {'о', 'е', 'а', 'и', 'н'}
        self.FREQ_EN = {'e', 't', 'a', 'o', 'i'}
        self.VOWELS_RU = set('аеёиоуыэюя')
        self.VOWELS_EN = set('aeiou')
    
    async def _get_bigram_score(self, text: str, lang_bigram: dict) -> float:
        '''
        Вычисление по биграммам(парам букв)
        '''
        _text_clean = re.sub(r'[^a-zа-яё]', '', text.lower())
        
        if len(_text_clean) < 2:
            return 0.0
        
        _bigrams = [_text_clean[i:i+2] for i in range(len(_text_clean) - 1)]
        if not _bigrams:
            return 0.0
        
        return sum(1 for bigram in _bigrams if bigram in lang_bigram) / len(_bigrams)

    
    async def _get_vowel_score(self, text: str, lang: str = 'ru') -> float:
        '''
        Вычисление соотношения гласных букв к итоговому числу символов
        '''
        _letters = [char for char in text.lower() if char.isalpha()]

        if not _letters:
            return 0.0
        
        return sum(1 for char in _letters if char in (self.VOWELS_RU if lang == 'ru' else self.VOWELS_EN)) / len(_letters)


    async def _get_freq_score(self, text: str, lang: str = 'ru') -> float:
        '''
        Вычисление частоты встреченных гласных в тексте, отсутствие которых, свидетельствует о том, что текст некорректный
        '''
        _text_clean = re.sub(r'[^a-zа-яё]', '', text.lower())

        if len(_text_clean) < 3:
            return 0.0
        
        _counter = Counter(_text_clean)
        _total = sum(_counter.values())

        return sum(_counter.get(char, 0) for char in (self.FREQ_RU if lang == 'ru' else self.FREQ_EN)) / _total


    async def _lang_likeness(self, text: str, lang: str = 'ru') -> float:
        '''
        Определение насколько введенный текст похож на текст целевого языка
        '''
        if len(text.strip()) < 3:
            return 0.0
        
        _bigram_score = await self._get_bigram_score(text, self.RU_BIGRAM if lang == 'ru' else self.EN_BIGRAM)
        _vowel_score = await self._get_vowel_score(text, lang)

        _target_vowel_score = 0.45 if lang == 'ru' else 0.40
        _vowel_score_normal = 1.0 - min(1.0, abs(_vowel_score - _target_vowel_score) / 0.3)
        _freq_score = await self._get_freq_score(text, lang)

        return 0.5 * _bigram_score + 0.3 * _vowel_score_normal + 0.2 * _freq_score
    
    
    async def _switch_layout(self, text: str, to_ru: bool = True) -> str:
        '''
        Переключение раскладки
        '''
        _layout = self.LAYOUT if to_ru else {v: k for k, v in self.LAYOUT.items()}
        return ''.join(_layout.get(char.lower(), char) for char in text)
    
    async def detect(self,
                     text: str,
                     autocorrect: bool = True) -> bool:
        '''
        Автоматическое определение необходимости переключения раскладки

        :param text: Входящий текст
        :type text: str

        :param autocorrect: Необходимость вернуть исправленный вариант
        :type autocorrect: bool
        '''

        if not text or len(text.strip()) < 3:
            return False
        
        _score_ru = await self._lang_likeness(text, 'ru')
        _score_en = await self._lang_likeness(text, 'en')

        _switched_ru = await self._switch_layout(text, to_ru = True)
        _switched_en = await self._switch_layout(text, to_ru = False)

        _switched_score_ru = await self._lang_likeness(_switched_ru, 'ru')
        _switched_score_en = await self._lang_likeness(_switched_en, 'en')

        best_orig = max(_score_ru, _score_en)
        best_switched = max(_switched_score_ru, _switched_score_en)

        need_switch = best_switched > best_orig + 0.2 and best_orig < 0.6

        # ---------- Защита от ложных срабатываний ----------
        # Если текст уже похож на русский (score_ru >= 0.1) или английский (score_en >= 0.1) и совсем не похож на противоположный язык (score_en/score_ru == 0),
        # Не переключаем раскладку
        if ((_score_ru >= 0.1 and _score_en == 0) or (_score_en >= 0.1 and _score_ru == 0)) and best_switched < 0.4:
            need_switch = False
        # ------------------------------------------------

        if not autocorrect:
            return need_switch
        
        if need_switch:
            _result = _switched_en
            if _switched_score_ru > _switched_score_en:
                _result = _switched_ru
            
            return {"changed_layout": _result}
        
        return False
        
