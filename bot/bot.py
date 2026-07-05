import os
import asyncio
import logging

from dotenv import load_dotenv
import twilight_vk
from twilight_vk.framework.rules import (
    TextRule,
    TrueRule,
    TwiMLRule,
    IsInvitedRule,
    AdminRule,
    IsAdminRule,
    ContainsRule,
    ReplyRule,
    ForwardRule,
    MentionRule,
    OnPayloadRule
)
from twilight_vk.utils.types.response import Response
from twilight_vk.utils.twiml import TwiML
from twilight_vk.utils.types.event_types import BotEventType

from modules.assocs import Assoc
from modules.database import DarkyDatabase
from modules.users import Users
from modules.chats import Chats
from modules.triggers import *
from modules.simplebot import SimpleCommands
from modules.witless import Witless
from custom_rules import *
from utils.sql import CheckSqlQueries
from utils.replies import Replies
from utils.layout import LayoutChanger
from utils import extractor

logger = logging.getLogger("darky-bot")
load_dotenv()

bot = twilight_vk.TwilightVK(
    bot_name="DarkyBot",
    token=os.getenv("ACCESS_TOKEN")
)

_db = DarkyDatabase()
bot_users = Users(_db, bot.methods)
bot_chats = Chats(_db, bot.methods)
witless = Witless()
assocs = Assoc(_db)
dorky_trigger = DorkyTrigger()
hello_trigger = HelloTrigger()
morning_trigger = MorningTrigger()
sleep_trigger = SleepTrigger()
twiml = TwiML()


''' ---------MIDDLEWARES--------- '''

@bot.middleware.pre
async def pre_middleware_handler(event: dict):
    
    if event.get("type", None) != BotEventType.MESSAGE_NEW:
        logger.debug(f"Event is not MESSAGE_NEW, no need to find assocs")
        return event

    return await assocs.check(event)


''' ---------REGISTRATION--------- '''

@bot.on_event.message_new(FromUser())
async def reg_user(event: dict):
    await bot_users.reg_user(event)

@bot.on_event.message_new(TextRule(value=["$darky reg"], ignore_case=True) & 
                          FromChat() & IsAdminRule() & (AdminRule() | IsBotAdmin(_db)))
async def reg_chat(event: dict):
    return await bot_chats.reg_chat(event)

@bot.on_event.message_new(FromChat() & IsAdminRule() & IsRegistered(_db))
async def reg_chat_member(event: dict):
    await bot_chats.reg_chat_member(event)


''' ---------USER SETTINGS--------- '''

@bot.on_event.message_new(TextRule(value=["$darky user settings"], ignore_case=True) & 
                          FromUser())
async def show_user_settings(event: dict):
    return await bot_users.get_user(event)

@bot.on_event.message_new(TwiMLRule(value=["$darky user set <key:word> <value:word>", "$darky user set <key:word>"], ignore_case=True) & 
                          FromUser())
async def update_user_settings(event: dict, key: str = None, value: str = None):
    return await bot_users.update_user(event, key, value)


''' ---------CHAT SETTINGS--------- '''

@bot.on_event.message_new(TextRule(value=["$darky chat settings"], ignore_case=True) & 
                          FromChat() & FromUser() & IsRegistered(_db) & (AdminRule() | IsBotAdmin(_db)))
async def show_chat_settings(event: dict):
    return await bot_chats.show_chat(event)

@bot.on_event.message_new(((TwiMLRule(value=["$darky stats <id>"], ignore_case=True) & MentionRule()) | 
                           (TextRule(value=["$darky stats"], ignore_case=True) & (ReplyRule() | ForwardRule()))) &
                          FromChat() & FromUser() & IsRegistered(_db))
async def show_chat_member_stats(event: dict, id: str = None, mentions: dict = None, have_reply: bool = None, have_forward: bool = None):
    member_id = (-mentions[0]["id"] if mentions[0]["type"] == "club" else mentions[0]["id"]) if mentions is not None and len(mentions) > 0 else False
    return await bot_chats.show_chat_member(event, member_id or extractor.extract_userid_from_reply(event, have_reply, have_forward))

@bot.on_event.message_new(TwiMLRule(value=["$darky chat set <key:word> <value>", "$darky chat set <key:word>"], ignore_case=True) & 
                          FromChat() & FromUser() & IsRegistered(_db) & (AdminRule() | IsBotAdmin(_db)))
async def update_chat_settings(event: dict, key: str = None, value: str = None):
    return await bot_chats.update_chat(event, key, value)


''' ---------ON EVERY MESSAGE EVENTS--------- '''

@bot.on_event.message_new(FromChat() & IsRegistered(_db))
async def update_chat_timestamp(event: dict):
    await bot_chats.update_timestamp(event)

@bot.on_event.message_new(FromChat() & IsRegistered(_db) & FromUser())
async def update_member_stats(event: dict):
    await bot_chats.update_member_stats(event)
    await bot_chats.note_activity(event)

@bot.on_event.message_new(FromUser())
async def update_user_timestamp(event: dict):
    await bot_users.update_timestamp(event)

@bot.on_event.message_new()
async def requests_handled_increment(event: dict):
    await _db.add_request_handled()


''' ---------MAIN--------- '''

@bot.on_event.message_new(TextRule(value=["$darky help"], ignore_case=True))
async def get_help(event: dict):
    '''
    Запрос руководства по использованию бота
    '''
    return Replies.HELP[0]

@bot.on_event.message_new(IsInvitedRule() & FromChat())
async def bot_greets(event: dict):
    '''
    Приветствие бота при добавлении в чат
    '''
    _peer_id = event["object"]["message"]["peer_id"]
    logger.info(f"Bot has been added to the chat {_peer_id}")
    return Response(
        peer_ids=_peer_id,
        message = Replies.BOT_GREETING[0],
        attachment = Replies.BOT_GREETING[1],
        keyboard = Replies.BOT_GREETING[2]
    )


''' ---------TRIGGERS--------- '''

@bot.on_event.message_new(ContainsRule(triggers = ["дурки", "дорки", "дорке", "дуркя", "dorky", "doorky", "dorke", "doorke"], ignore_case = True, need_list = False) &
                          (~FromChat() | (FromChat() & (~IsRegistered(_db) | IsRegistered(_db) & SQLRule(_db._db_client,
                                                                                                         query = CheckSqlQueries.TRIGGER_CHECK,
                                                                                                         key = "triggers", value = True)))))
async def trigger1(event: dict):
    return dorky_trigger.react()

@bot.on_event.message_new(ContainsRule(triggers = ['прив', 'привет', 'приветствую', 'здравствуйте', 'преет', 'преть', 'приветик', 'приветики', 'здрасте', 'хай', 'хелло', 'добрый день', 'добрый вечер'], ignore_case = True, need_list = False) &
                          (~FromChat() | (FromChat() & (~IsRegistered(_db) | IsRegistered(_db) & SQLRule(_db._db_client,
                                                                                                         query = CheckSqlQueries.TRIGGER_CHECK,
                                                                                                         key = "triggers", value = True)))))
async def trigger2(event: dict):
    return hello_trigger.react()

@bot.on_event.message_new(ContainsRule(triggers = ['утра', 'утречка', 'утро', 'доброе утро', 'проснулся', 'проснулась', 'добре', 'проснувся', 'проснувась', 'поспал', 'спал'], ignore_case = True, need_list = False) &
                          (~FromChat() | (FromChat() & (~IsRegistered(_db) | IsRegistered(_db) & SQLRule(_db._db_client,
                                                                                                         query = CheckSqlQueries.TRIGGER_CHECK,
                                                                                                         key = "triggers", value = True)))))
async def trigger3(event: dict):
    return morning_trigger.react()

@bot.on_event.message_new(ContainsRule(triggers = ['спокойной', 'ночи', 'споки', 'споке', 'ночки', 'снов', 'спать', 'посплю'], ignore_case = True, need_list = False) &
                          (~FromChat() | (FromChat() & (~IsRegistered(_db) | IsRegistered(_db) & SQLRule(_db._db_client,
                                                                                                         query = CheckSqlQueries.TRIGGER_CHECK,
                                                                                                         key = "triggers", value = True)))))
async def trigger4(event: dict):
    return sleep_trigger.react()


''' ---------SIMPLE COMMANDS--------- '''

@bot.on_event.message_new(TwiMLRule(value=["$darky try <action>"], ignore_case=True))
async def bot_try(event: dict, action: str):
    return SimpleCommands.try_command(action)

@bot.on_event.message_new(TwiMLRule(value=["$darky choose <variables:any>"], ignore_case=True))
async def bot_choose(event: dict, variables: str):
    return SimpleCommands.choice_command(variables)

@bot.on_event.message_new(TwiMLRule(value=["$darky guess <user_event>"], ignore_case=True))
async def bot_guess(event: dict, user_event: str):
    return SimpleCommands.guess_command(user_event)

@bot.on_event.message_new((TextRule(value=["$darky roll"], ignore_case=True) | TwiMLRule(value=["$darky roll <rolls:int>"], ignore_case=True)))
async def roll(event: dict, rolls: int = 1):
    return SimpleCommands.roll(rolls)

@bot.on_event.message_new(LayoutRule() & 
                          (~FromChat() | (FromChat() & (~IsRegistered(_db) | IsRegistered(_db) & SQLRule(_db._db_client,
                                                                                                         query = CheckSqlQueries.LAYOUT_AUTODETECT_CHECK,
                                                                                                         key = "layout_autodetect", value = True)))))
async def autocorrection_layout(event: dict, changed_layout: str = None):
    return f"🧐 Возможно вы использовали неправильную раскладку клавиатуры\nЯ исправила текст за вас.\n\nИзмененный текст:\n{changed_layout}"

@bot.on_event.message_new(TextRule(value=["$darky layout"], ignore_case = True) & (ReplyRule() | ForwardRule()))
@bot.on_event.message_new(TwiMLRule(value=["$darky layout <text>"], ignore_case = True))
async def change_layout_text(event: dict, text: str = None, have_reply: bool = None, have_forward: bool = None):
    return await SimpleCommands.layout(text or extractor.extract_text_from_reply(event, have_reply, have_forward))


''' ---------ASSOCS--------- '''

@bot.on_event.message_new(TwiMLRule(value=["$darky assoc <command> = <assoc>"], ignore_case = True) & 
                          FromChat() & FromUser() & IsRegistered(_db) & (AdminRule() | IsBotAdmin(_db)))
async def assoc_add_handler(event: dict, command: str = None, assoc: str = None):
    return await assocs.add(event, command, assoc)

@bot.on_event.message_new(TwiMLRule(value=["$darky assoc del <assoc>"], ignore_case = True) &
                          FromChat() & FromUser() & IsRegistered(_db) & (AdminRule() | IsBotAdmin(_db)))
async def assoc_del_handler(event: dict, assoc: str = None):
    return await assocs.delete(event, assoc)


''' ---------DARKY-SPEAK--------- '''

@bot.on_event.message_new(TrueRule())
async def speak_handler_push(event: dict):
    await witless.push(event)
    return await witless.generate(event, size="small")

@bot.on_event.message_new((TextRule(value=["$darky speak"], ignore_case=True) | TwiMLRule(value=["$darky speak <size:word>"], ignore_case=True)))
async def speak_handler(event: dict, size: str = "any"):
    if size in ["small", "medium", "large", "any"]:
        return await witless.generate(event, size=size, on_self = False)

@bot.on_event.message_new(TextRule(value=["$darky bugurt"], ignore_case=True))
async def bugurt_handler(event: dict):
    return await witless.bugurt(event)

@bot.on_event.message_new(TextRule(value=["$darky speak data"], ignore_case=True))
async def speak_data_handler(event: dict):
    return await witless.info(event)

@bot.on_event.message_new(TextRule(value=["$darky speak wipe"], ignore_case=True) & (AdminRule() | IsBotAdmin(_db)) & FromChat())
@bot.on_event.message_new(TextRule(value=["$darky speak wipe"], ignore_case=True) & ~FromChat())
async def wipe_speak_data(event: dict):
    return await witless.wipe(event["object"]["message"]["peer_id"])


''' ---------TEST COMMANDS--------- '''

@bot.on_event.message_new(TextRule(value=["hello world"]) & Disabled())
async def test(event: dict):
    return "Hello world"


''' ---------BUTTONS HANDLING--------- '''

@bot.on_event.raw(BotEventType.MESSAGE_EVENT, 
                  ~OnPayloadRule(payload={"darky_button": "help"}) & 
                  ~OnPayloadRule(payload={"darky_button": "reg_chat"}) &
                  OnPayloadRule())
async def button_test(event: dict):
    await bot.methods.messages.sendMessageEventAnswer(event["object"]["event_id"],
                                                      event["object"]["user_id"],
                                                      event["object"]["peer_id"])
    return Replies.UNDER_DEVELOPMENT[0]

@bot.on_event.raw(BotEventType.MESSAGE_EVENT,
                  OnPayloadRule(payload={"darky_button": "reg_chat"}) &
                  FromChat() & IsAdminRule() & (AdminRule() | IsBotAdmin(_db)))
async def reg_chat_button(event: dict):
    await bot.methods.messages.sendMessageEventAnswer(event["object"]["event_id"],
                                                      event["object"]["user_id"],
                                                      event["object"]["peer_id"])
    return await bot_chats.reg_chat(event)

@bot.on_event.raw(BotEventType.MESSAGE_EVENT, OnPayloadRule(payload={"darky_button": "help"}))
async def help_button(event: dict):
    await bot.methods.messages.sendMessageEventAnswer(event["object"]["event_id"],
                                                      event["object"]["user_id"],
                                                      event["object"]["peer_id"])
    return Replies.HELP[0]

@bot.on_event.raw(BotEventType.MESSAGE_EVENT,
                  OnPayloadRule(payload={"darky_button": "reg_chat"}) &
                  FromChat() & ~IsAdminRule())
async def bot_is_not_admin_button(event: dict):
    await bot.methods.messages.sendMessageEventAnswer(event["object"]["event_id"],
                                                      event["object"]["user_id"],
                                                      event["object"]["peer_id"])
    return Replies.BOT_IS_NOT_ADMIN[0], Replies.BOT_IS_NOT_ADMIN[2]

@bot.on_event.raw(BotEventType.MESSAGE_EVENT,
                  OnPayloadRule(payload={"darky_button": "reg_chat"}) &
                  FromChat() & IsAdminRule() & (~AdminRule() & ~IsBotAdmin(_db)))
async def access_denied_button(event: dict):
    await bot.methods.messages.sendMessageEventAnswer(event["object"]["event_id"],
                                                      event["object"]["user_id"],
                                                      event["object"]["peer_id"])
    return Replies.ACCESS_DENIED[0], Replies.ACCESS_DENIED[2]


''' ---------WRONG USE COMMANDS--------- '''

@bot.on_event.message_new((TextRule(value=["$darky try",
                                          "$darky choose",
                                          "$darky guess",
                                          "$darky chat set",
                                          "$darky user set",
                                          "$darky assoc",
                                          "$darky assoc del"], ignore_case=True)) |
                          ((TwiMLRule(value=["$darky stats <id>"], ignore_case=True)) & ~MentionRule(need_list=False)) |
                          (TextRule(value=["$darky stats"], ignore_case=True) & ~ReplyRule() & ~ForwardRule()))
async def wrong_usage_handle(event: dict, **kwargs):
    return Replies.WRONG_USAGE[0], Replies.WRONG_USAGE[2]

@bot.on_event.message_new((TextRule(value=["$darky reg",
                                          "$darky chat settings",
                                          "$darky stats",
                                          "$darky chat set",
                                          "$darky assoc",
                                          "$darky assoc del"], ignore_case=True) | 
                          TwiMLRule(value=["$darky stats <id>",
                                           "$darky chat set <params>",
                                           "$darky assoc <params>",
                                           "$darky assoc del <params>"], ignore_case=True)) &
                          ~FromChat())
async def not_from_chat_handle(event: dict, **kwargs):
    return Replies.NOT_WORK_HERE[0], Replies.NOT_WORK_HERE[2]

@bot.on_event.message_new((TextRule(value=["$darky chat settings",
                                           "$darky stats",
                                           "$darky chat set",
                                           "$darky assoc",
                                           "$darky assoc del"], ignore_case=True) | 
                          TwiMLRule(value=["$darky stats <id>",
                                           "$darky chat set <params>",
                                           "$darky assoc <params>",
                                           "$darky assoc del <params>"], ignore_case=True)) &
                          FromChat() & ~IsRegistered(_db))
async def not_registered_chat_handle(event: dict, **kwargs):
    _peer_id = event["object"]["message"]["peer_id"]
    _conversation_message_id = event["object"]["message"]["conversation_message_id"]
    return Response(
        peer_ids = _peer_id,
        forward={
            "is_reply": True,
            "peer_id": _peer_id,
            "conversation_message_ids": _conversation_message_id
        },
        message = Replies.CHAT_IS_NOT_REGISTERED[0],
        keyboard = Replies.CHAT_IS_NOT_REGISTERED[2]
    )

@bot.on_event.message_new((TextRule(value=["$darky reg",
                                           "$darky chat settings",
                                           "$darky chat set"], ignore_case=True) |
                          TwiMLRule(value=["$darky chat set <params>"], ignore_case=True)) & 
                          FromChat() & ~IsAdminRule())
async def bot_is_not_admin_reply(event: dict, **kwargs):
    return Replies.BOT_IS_NOT_ADMIN[0], Replies.BOT_IS_NOT_ADMIN[2]

@bot.on_event.message_new((TextRule(value=["$darky reg", 
                                           "$darky layout",
                                           "$darky chat settings",
                                           "$darky chat set",
                                           "$darky assoc",
                                           "$darky assoc del"], ignore_case=True) | 
                          TwiMLRule(value=["$darky layout <text>",
                                           "$darky chat set <params>",
                                           "$darky assoc <params>",
                                           "$darky assoc del <params>"], ignore_case=True)) & 
                          FromChat() & (~AdminRule() & ~IsBotAdmin(_db)))
async def access_denied_reply(event: dict, **kwargs):
    return Replies.ACCESS_DENIED[0], Replies.ACCESS_DENIED[2]

bot.start()