from random import choice, random

cdef str _start = "___start___"
cdef str _end = "___end___"


def generate(list samples, int tries_count, int size,
             context=None, float continue_probability=0.5):
    if not samples:
        return None

    # Построение модели
    frame_map = {}
    start_frames = []
    msg_words = [s.split() for s in samples if s.strip()]
    if not msg_words:
        return None

    for i, words in enumerate(msg_words):
        frame_map.setdefault(_start, []).append(words[0])
        start_frames.append(words[0])
        for j in range(len(words) - 1):
            frame_map.setdefault(words[j], []).append(words[j + 1])
        frame_map.setdefault(words[-1], []).append(_end)
        if i < len(msg_words) - 1:
            frame_map.setdefault(_end, []).append(msg_words[i + 1][0])

    for _ in range(tries_count):
        # Начальное слово
        if context is not None:
            if isinstance(context, str):
                ctx_msgs = [context]
            else:
                ctx_msgs = list(context)
            if not ctx_msgs:
                continue
            last_words = ctx_msgs[-1].split()
            if not last_words:
                continue
            start_word = last_words[-1]
            if start_word not in frame_map:
                continue
        else:
            start_word = choice(start_frames)

        current_msg = []
        all_msgs = []
        total_words = 0
        current_word = start_word
        if context is None:
            current_msg.append(start_word)
            total_words += 1

        # Генерация с ограничением: максимум 2 сообщения, если context задан
        max_msgs = 2 if context is not None else 5
        msg_count = 0

        while True:
            if current_word not in frame_map:
                break

            next_word = choice(frame_map[current_word])

            if next_word == _end:
                if current_msg:
                    all_msgs.append(" ".join(current_msg))
                    current_msg = []
                    msg_count += 1
                if msg_count >= max_msgs:
                    break
                if random() < continue_probability:
                    # Выбираем следующее начало
                    if _end in frame_map:
                        next_start = choice(frame_map[_end])
                    else:
                        next_start = choice(start_frames)
                    current_msg.append(next_start)
                    total_words += 1
                    current_word = next_start
                else:
                    break
            else:
                current_msg.append(next_word)
                total_words += 1
                current_word = next_word
                if total_words >= 100:
                    break

        if current_msg:
            all_msgs.append(" ".join(current_msg))
            msg_count += 1

        if not all_msgs:
            continue

        # Проверка размера
        if size == 0:
            if total_words > 100:
                continue
        elif size == 1:
            if not (2 <= total_words <= 3):
                continue
        elif size == 2:
            if not (4 <= total_words <= 7):
                continue
        elif size == 3:
            if not (8 <= total_words <= 100):
                continue
        else:
            raise ValueError("Size must be 0, 1, 2 or 3")

        # Проверка дубликатов (только если context не задан)
        if context is None:
            if len(all_msgs) == 1 and all_msgs[0] in samples:
                continue

        return "\n".join(all_msgs)

    return None