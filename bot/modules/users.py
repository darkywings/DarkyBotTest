from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from twilight_vk.framework.methods import VkMethods
    from modules.database import DarkyDatabase

logger = logging.getLogger("bot-users")

class Users:

    def __init__(self,
                 db_client: 'DarkyDatabase',
                 methods: 'VkMethods'
                 ):
        self._db = db_client
        self._methods = methods

    async def reg_user(self, event: dict) -> None:
        '''
        Регистрация пользователя в базе данных
        '''
        _user_id = event["object"]["message"]["from_id"]

        logger.debug(f"Checking registration for user {_user_id}...")
        if await self._db.check_registration("user", _user_id):
            logger.debug(f"User {_user_id} is already registered")
            return
        
        logger.debug(f"Registering user {_user_id}...")
        user = await self._methods.users.get(
            user_ids = _user_id,
            fields = "screen_name"
        )["response"][0]
        await self._db.register_user(_user_id, user["first_name"], user["last_name"], user["screen_name"])

        logger.info(f"User {_user_id} was registered")