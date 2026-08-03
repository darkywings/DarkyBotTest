import os
import logging
import random

import dotenv
from twilight_vk.http.async_http import Http
from twilight_vk.utils.types.response import Response

from utils.replies import Replies

dotenv.load_dotenv()
logger = logging.getLogger('witless')

WITLESS_HOST = os.getenv("WITLESS_HOST", "witless-api")
WITLESS_PORT = os.getenv("WITLESS_PORT", 8000)

class Witless:

    def __init__(self):
        self.http = Http()

    async def speak(self, event: dict, size: str = "any") -> Response:
        '''
        Интерфейс для генерации через $darky speak
        '''
        _peer_id = event["object"]["message"]["peer_id"]
        _conversation_message_id = event["object"]["message"]["conversation_message_id"]

        result_message = await self._generate(
            peer_id = _peer_id,
            size = size,
            context = None
        )

        return Response(
            peer_ids = _peer_id,
            forward = {
                "is_reply": True,
                "peer_id": _peer_id,
                "conversation_message_ids": _conversation_message_id
            },
            message = result_message,
            keyboard = Replies.WITLESS_GENERATE_FAIL[2] if result_message == Replies.WITLESS_GENERATE_FAIL[0] else None
        )

    async def random_speak(self, peer_id: int = None, context: str = None) -> Response:
        '''
        Рандомная генерация сообщений
        '''
        if random.randint(0, 15) != 0:
            return
        
        if peer_id is None:
            # TODO: get randomized peer_id
            # TODO: get last message from that peer
            peer_id = 0

        result_message = await self._generate(
            peer_id = peer_id,
            size = "smallest",
            context = context
        )

        if result_message != Replies.WITLESS_GENERATE_FAIL[0]:
            return Response(
                peer_ids = peer_id,
                message = result_message,
            )
        
        return

    async def _generate(self, 
                        peer_id: int,
                        size: str = "any",
                        context: str = None) -> str:
        '''
        Получает сгенерированный текст с backend
        '''
        logger.debug(f"Generating on peer_id: {peer_id}...")
        response = await self.http.get(
            url = f"http://{WITLESS_HOST}:{WITLESS_PORT}/generate",
            json = {"peer_id": peer_id, "size": size, "context": context},
            raw = False
        )

        if "success" in response.keys() and response["success"]:
            result = response["result"]
            logger.debug(f"Generated message on peer_id: {peer_id} = {result}")

            return result
        
        logger.debug(f"Failed to generate message on peer_id: {peer_id}")
        return Replies.WITLESS_GENERATE_FAIL[0]
    
    async def bugurt(self, event: dict) -> str:
        '''
        Генерирует в стиле бугурта
        '''
        _peer_id = event["object"]["message"]["peer_id"]
        _conversation_message_id = event["object"]["message"]["conversation_message_id"]
        
        _parts = []

        logger.debug(f"Generating bugurt for peer_id: {_peer_id}...")

        context = None
        for i in range(random.randint(3, 10)):
            response = await self.http.get(
                url = f"http://{WITLESS_HOST}:{WITLESS_PORT}/generate",
                json = {"peer_id": _peer_id, "size": "md", "context": context},
                raw = False
            )
            if "success" in response.keys() and response["success"]:
                context = response["result"]
                _parts.append(response["result"].upper())
                continue
            
            logger.debug(f"Failed to generate bugurt on peer_id: {_peer_id}")
            return Response(
                peer_ids = _peer_id,
                forward = {
                    "is_reply": True,
                    "peer_id": _peer_id,
                    "conversation_message_ids": _conversation_message_id
                },
                message = Replies.WITLESS_GENERATE_FAIL[0],
                keyboard = Replies.WITLESS_GENERATE_FAIL[2]
            )
        
        _result = "\n@\n".join(_parts)
        logger.debug(f"Generated bugurt on peer_id: {_peer_id} = {_result}")
        return _result

    async def info(self, event: dict) -> str:
        '''
        Выводит количество сохраненных строк для обучения
        '''
        _peer_id = event["object"]["message"]["peer_id"]
        _conversation_message_id = event["object"]["message"]["conversation_message_id"]

        logger.debug(f"Asked info for {_peer_id}")

        response = await self.http.get(
            url = f"http://{WITLESS_HOST}:{WITLESS_PORT}/count",
            json = {"peer_id": _peer_id},
            raw = False
        )

        if "success" in response.keys() and response["success"]:
            return Response(
                peer_ids = _peer_id,
                forward = {
                    "is_reply": True,
                    "peer_id": _peer_id,
                    "conversation_message_ids": _conversation_message_id
                },
                message = f"Сохранено {response['result']} строк для обучения. \nЕсли это число не увеличивается, проверьте, выдали ли вы мне доступ ко всей переписке",
                keyboard = Replies.WITLESS_ON_INFO[2]
            )
        
        return "Произошла неизвестная ошибка"

    async def wipe(self, peer_id: int) -> str:
        '''
        Сбрасывает данные для обучения
        '''
        logger.debug(f"Asked for wipe data for {peer_id}")

        response = await self.http.get(
            url = f"http://{WITLESS_HOST}:{WITLESS_PORT}/wipe",
            json = {"peer_id": peer_id},
            raw = False
        )

        if "success" in response.keys() and response["success"]:
            logger.debug(f"All data for {peer_id} was wiped")
            return "❕ Данные для обучения в этой беседе были сброшены"
        
        logger.debug(f"{peer_id} don't have any data for wipe")
        return "⚠️ Нет данных для обучения, мне нечего сбрасывать"

    async def push(self, event: dict) -> None:
        '''
        Сохранение сообщений для обучения
        '''
        _peer_id = event["object"]["message"]["peer_id"]
        _text = event["object"]["message"]["default_text"]

        if len(_text.split(' ')) > 1 and len(_text) <= 400:

            logger.debug(f"Pushing data for {_peer_id}...")

            await self.http.get(
                url = f"http://{WITLESS_HOST}:{WITLESS_PORT}/push",
                json = {"peer_id": _peer_id, "message": _text.lower()}
            )

        return