from random import choice, randint

cdef str _start = "___start___"
cdef str _end = "___end___"


def generate(list samples, int tries_count, int size, str context=None):
    if not samples:
        return None

    cdef list frames = []
    cdef list start_frames = []
    cdef dict frame_map = {}
    cdef list words
    cdef list result
    cdef str str_result
    cdef str next_frame
    cdef str sample
    cdef int i

    # Построение марковской цепи
    for sample in samples:
        words = sample.split(" ")
        frames.append(_start)
        for word in words:
            frames.append(word)
        frames.append(_end)

    for i in range(len(frames)):
        if frames[i] != _end:
            try:
                frame_map[frames[i]].append(frames[i + 1])
            except KeyError:
                frame_map[frames[i]] = [frames[i + 1]]
            if frames[i] == _start:
                start_frames.append(frames[i + 1])

    # Обработка контекста: если он невалидный, игнорируем его
    cdef list context_words = None
    if context is not None:
        context_words = context.split(" ")
        # Проверяем валидность
        valid = True
        if _end in context_words:
            valid = False
        else:
            for w in context_words[:-1]:
                if w not in frame_map:
                    valid = False
                    break
            if valid and (not context_words or context_words[-1] not in frame_map):
                valid = False
        if not valid:
            # Контекст невалидный – сбрасываем, будем генерировать с нуля
            context_words = None

    # Максимальная длина для предотвращения бесконечного цикла
    max_len = 100

    for i in range(tries_count):
        if context_words is None:
            result = [choice(start_frames)]
        else:
            result = context_words.copy()

        added = False
        idx = 0
        while idx < len(result) and len(result) <= max_len:
            frame = result[idx]
            next_frame = choice(frame_map[frame])
            if next_frame == _end:
                break
            else:
                result.append(next_frame)
                added = True
            idx += 1

        # Если контекст был задан, но не добавлено ни одного слова – попытка не засчитывается
        if context is not None and context_words is not None and not added:
            continue

        str_result = " ".join(result)

        if context is not None and str_result.startswith(context) and randint(0, 5) > 2 and added:
            str_result = "".join(str_result[len(context):])

        if str_result not in samples:
            if size == 0:  # любой
                if len(result) <= 100:
                    return str_result
            elif size == 1:  # малый
                if 2 <= len(result) <= 3:
                    return str_result
            elif size == 2:  # средний
                if 4 <= len(result) <= 7:
                    return str_result
            elif size == 3:  # большой
                if 8 <= len(result) <= 100:
                    return str_result
            elif size == 4: # маленький, но без нижнего лимита
                if len(result) <= 3:
                    return str_result
            else:
                raise ValueError("Size must be 0, 1, 2 or 3")

    return None