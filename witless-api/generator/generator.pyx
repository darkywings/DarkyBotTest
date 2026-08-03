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
    for i in