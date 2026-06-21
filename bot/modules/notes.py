class Notes:

    def __init__(self):
        pass

    async def show_list(self, event: dict, page: int):
        pass

    async def show(self, event: dict, id: int):
        pass

    async def add(self, event: dict, title: str, content: str):
        pass

    async def delete(self, event: dict, id: int):
        pass

    async def edit(self, event: dict, id: int, content: str):
        pass

    async def rename(self, event: dict, id: int, title: str):
        pass