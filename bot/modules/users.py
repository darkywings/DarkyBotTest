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
                 ) -> None:
        self._db = db_client
        self._methods = methods

    async def reg_user(self, event: dict) -> None:
        '''
        Регистрация пользователя в базе данных
        '''
        _user_id = event["object"]["message"]["from_id"]

        if _user_id < 0:
            logger.warning(f"{_user_id} is not user")
            return

        logger.debug(f"Checking registration for user {_user_id}...")
        if await self._db.check_registration("user", _user_id):
            logger.debug(f"User {_user_id} is already registered")
            return
        
        logger.debug(f"Registering user {_user_id}...")
        user = await self._methods.users.get(
            user_ids = _user_id,
            fields = "screen_name"
        )
        user = user["response"][0]
        await self._db.register_user(_user_id, user["first_name"], user["last_name"], user["screen_name"])

        logger.info(f"User {_user_id} was registered")
    
    async def get_user(self, event: dict) -> str:
        '''
        Отображение информации о пользователе и его настройках
        '''
        _user_id = event["object"]["message"]["from_id"]
        
        logger.debug(f"Getting the user {_user_id}...")
        _user = await self._db.get_user(_user_id)

        if _user == False:
            return f"⚠️ Я не нашла данные о вашей регистрации"

        return (
            f"🧾 Информация о вас:\n" \
            f" 🔹 ID: {_user["user_id"]}\n" \
            f" 🔹 ID в боте: {_user["id"]}\n" \
            f" 🔹 Имя: {_user["first_name"]} {_user["last_name"]}\n" \
            f" 🔹 Короткое имя: {_user["screen_name"]}\n"
            f"⚙️ Ваши настройки:\n"
            f" 🔹 Оповещения об обновлениях: {_user["update_notifications"]}\n" \
            f" 🔹 Упоминания ботом: {_user["mentions"]}\n" \
            f" 🔹 РП: ❕ {_user["who_can_rp_me"]}\n" \
            f" 🔹 Предупреждения DarkyVerify: ❕ {_user["darky_verify_warns"]}\n" \
            f" 🔹 Забанен DarkyVerify: {_user["is_banned"]}".relpace("True", "✅").replace("False", "❌")
        )

    async def update_user(self, event: dict, key: str, value: str) -> None:
        '''
        Изменение настройки пользователя
        '''

        if key in [
            "update_notifications",
            "mentions",
            "who_can_rp_me"
        ]:
            if (key in ["update_notifications", "mentions"] and not isinstance(value, bool) or 
                key in ["who_can_rp_me"] and value not in ["all", "only_bot", "only_users", "nobody"]):
                return "⚠️ Неверное значение для параметра, убедитесь в правильности значения"
            
            await self._db.update_user(event["object"]["message"]["from_id"], key, value)
            return f"✅ Параметр {key} установлен на - {value}"

        return "❌ Такого параметра не существует, либо он меняется не этим путем"