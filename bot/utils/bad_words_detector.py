import re

BAD_WORDS = [
    "хуй", "хуя", "хуи", "хуе", "бля", "пизд", "сук", "мудак", "еба", "ебу", "еби", "ебл", 
    "пидор", "пидр", "шлюх", "шалав", "залуп", "манд", "хер", "говн", "дерьм"
]

def extract_bad_words(text: str) -> dict:

    clean = text.lower().replace('ё', 'е')

    tokens = re.findall(r'[а-яa-z]+', clean)

    total = 0
    words = []

    for token in tokens:
        for root in BAD_WORDS:
            if root in token:
                total += 1
                if token not in words: words.append(token)
    
    return {"count": total, "items": words}