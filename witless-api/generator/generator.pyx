from random import choice, random


cdef str _start = "___start___"
cdef str _end = "___end___"


def generate(list samples, int tries_count, int size,
             str context=None, double context_prob=0.7):
    """
    samples      — список сообщений (в порядке появления в чате)
    tries_count  — сколько попыток генерации
    size         — 0=any, 1=small(2-3), 2=medium(4-7), 3=large(8-100)
    context      — опциональный контекст (последнее сообщение / фраза)
    context_prob — вероятность попытаться продолжить context (0.0–1.0)
    """
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
    cdef str prev_last = None          # последнее слово предыдущего сообщения
    cdef int i

    # ---------- построение модели ----------
    for sample in samples:
        words = sample.split()
        if not words:
            continue

        # обычная цепочка внутри сообщения
        frames.append(_start)
        for word in words:
            frames.append(word)
        frames.append(_end)

        # связь соседних сообщений
        if prev_last is not None:
            first_word = words[0]
            try:
                frame_map[prev_last].append(first_word)
            except KeyError:
                frame_map[prev_last] = [first_word]

        prev_last = words[-1]

    # заполняем frame_map и start_frames
    for i in range(len(frames)):
        if frames[i] != _end:
            try:
                frame_map[frames[i]].append(frames[i + 1])
            except KeyError:
                frame_map[frames[i]] = [frames[i + 1]]

            if frames[i] == _start:
                start_frames.append(frames[i + 1])

    if not start_frames:
        return None

    # ---------- генерация ----------
    for _ in range(tries_count):
        use_context = False
        result = []

        # решаем, продолжать ли контекст
        if (context and context.strip()
                and random() < context_prob):
            ctx_words = context.strip().split()
            if ctx_words:
                last = ctx_words[-1]
                if last in frame_map:
                    result = [last]
                    use_context = True

        # если контекст не подошёл — обычный старт
        if not result:
            result = [choice(start_frames)]

        # генерируем продолжение
        while True:
            current = result[-1]
            if current not in frame_map:
                break

            next_frame = choice(frame_map[current])
            if next_frame == _end:
                break
            result.append(next_frame)

            # защита от слишком длинных цепочек
            if len(result) > 120:
                break

        # если начинали с контекста — убираем первое слово (оно уже было в сообщении пользователя)
        if use_context and len(result) > 1:
            result = result[1:]

        if not result:
            continue

        str_result = " ".join(result)

        # проверка размера
        length_ok = False
        if size == 0:          # any
            length_ok = len(result) <= 100
        elif size == 1:        # small
            length_ok = 2 <= len(result) <= 3
        elif size == 2:        # medium
            length_ok = 4 <= len(result) <= 7
        elif size == 3:        # large
            length_ok = 8 <= len(result) <= 100
        else:
            raise ValueError("Size must be 0, 1, 2 or 3")

        if not length_ok:
            continue

        # фильтр уникальности отключаем, если генерация шла от контекста
        if use_context or str_result not in samples:
            return str_result

    return None