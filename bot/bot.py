import os
import asyncio
import logging

from dotenv import load_dotenv
import twilight_vk
from twilight_vk.framework.rules import (
    TextRule,
    TrueRule,
    TwiMLRule,
    IsInvitedRule
)
from twilight_vk.utils.types.response import Response

from modules.database import DarkyDatabase
from modules.triggers import TriggerReplies
from modules.simplebot import SimpleCommands
from custom_rules import *

load_dotenv()

bot = twilight_vk.TwilightVK(
    BOT_NAME="DarkyBot",
    ACCESS_TOKEN=os.getenv("ACCESS_TOKEN")
)
bot_db = DarkyDatabase()


@bot.on_event.message_new(TrueRule())
async def reg_user(event: dict):
    '''
    Регистрация пользователя при первом его сообщении
    '''
    _user_id = event["object"]["message"]["from_id"]
    
    bot.logger.debug(f"Registrating user {_user_id}...")

    if await bot_db.check_registration("user", _user_id):
        bot.logger.debug(f"User {_user_id} was already registered!")
        return

    await bot_db.register_user(_user_id)

    bot.logger.info(f"User {_user_id} was successfully registered!")

@bot.on_event.message_new(FromChat() and IsInvitedRule())
async def bot_greets(event: dict):
    '''
    Приветствие бота при добавлении в чат
    '''
    _peer_id = event["object"]["message"]["peer_id"]
    bot.logger.info(f"Bot has been added to the chat {_peer_id}")
    return Response(
        peer_ids=_peer_id,
        message="Привет, я бот :>"
    )

@bot.on_event.message_new(FromChat() and TextRule(value=["$darky reg"], ignore_case=True))
async def reg_chat(event: dict):
    '''
    Регистрация чата
    '''
    _peer_id = event["object"]["message"]["peer_id"]

    bot.logger.debug(f"Registrating chat {_peer_id}...")

    is_registered = await bot_db.check_registration("chat", _peer_id)
    if is_registered:
        bot.logger.debug(f"Chat {_peer_id} was already registered!")
        return "⚠️Ваша беседа уже была ранее зарегистрирована"

    conversation_data = await bot.methods.messages.getConversationById(
        peer_ids = _peer_id
    )
    await bot_db.register_chat(_peer_id, conversation_data["response"]["items"][0]["chat_settings"]["title"])

    bot.logger.info(f"Chat {_peer_id} was successfully registered!")
    return "✅Ваша беседа была успешно зарегистрирована"

@bot.on_event.message_new(TwiMLRule(value=["$darky show reg <obj_type:word>"], ignore_case=True))
async def show_reg(event: dict, obj_type: str):

    allowed_tables = {"user", "chat"}
    
    if obj_type not in allowed_tables:
        return f"❌ Неизвестный тип: {obj_type}. Доступно: {', '.join(allowed_tables)}"
    
    _type = obj_type
    _obj_id = event["object"]["message"]["peer_id"] if obj_type == "chat" else event["object"]["message"]["from_id"]
    
    try:
        record = await bot_db.check_registration(obj_type = _type,
                                                 obj_id = _obj_id, 
                                                 only_bool = False)
        
        if not record:
            return f"📭 Запись {obj_type} с ID {_obj_id} не найдена"
        
        response = f"📋 Запись в таблице '{obj_type}':\n"
        response += f"🔑 ID: {_obj_id}\n"
        
        for key, value in record.items():
            if key != f"{_type}_id" and value is not None:
                response += f"• {key}: {value}\n"
        
        return response
        
    except Exception as e:
        return f"❌ Ошибка: {str(e)[:100]}"
    
@bot.on_event.message_new(Disabled() and TextRule(value=["hello world"]))
async def test(event: dict):
    return "Hello world"

@bot.on_event.message_new(DorkyTrigger())
async def dork_trigger(event: dict):
    return TriggerReplies.dorky()
        
@bot.on_event.message_new(TwiMLRule(value=["$darky try <action>"], ignore_case=True))
async def bot_try(event: dict, action: str):
    return SimpleCommands.try_command(action)

@bot.on_event.message_new(TwiMLRule(value=["$darky choose <variables:any>"], ignore_case=True))
async def bot_try(event: dict, variables: str):
    return SimpleCommands.choice_command(variables)

@bot.on_event.message_new(TwiMLRule(value=["$darky guess <user_event>"], ignore_case=True))
async def bot_try(event: dict, user_event: str):
    return SimpleCommands.guess_command(user_event)

@bot.on_event.message_new(TwiMLRule(value=["$darky roll <rolls:int>", "$darky roll"], ignore_case=True))
async def roll(event: dict, rolls: int = 1):
    return SimpleCommands.roll(rolls)

@bot.on_event.message_new(TextRule(value=["$darky stop", "дарки стоп"], ignore_case=True))
async def stop(event: dict):
    await bot_db.close()
    bot.should_stop()
    return "Останавливаюсь"

bot.start()