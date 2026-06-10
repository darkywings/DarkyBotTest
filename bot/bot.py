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
from modules.users import Users
from modules.triggers import TriggerReplies
from modules.simplebot import SimpleCommands
from custom_rules import *

load_dotenv()

bot = twilight_vk.TwilightVK(
    bot_name="DarkyBot",
    token=os.getenv("ACCESS_TOKEN")
)
bot_db = DarkyDatabase()

bot_users = Users(bot_db, bot.methods)

@bot.on_event.message_new(TrueRule())
async def reg_user(event: dict):
    await bot_users.reg_user(event)

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

@bot.on_event.message_new(TwiMLRule(value=["$darky show reg <obj_type:word> <id:int>"], ignore_case=True))
async def show_reg(event: dict, obj_type: str, id: int):
    try:
        result = await bot_db.check_registration(obj_type, id)
        return f"Запись в базе данных\n{result}"
    except ValueError as e:
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