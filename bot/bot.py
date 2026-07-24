import os
import asyncio
import logging

from dotenv import load_dotenv
import twilight_vk
from twilight_vk.framework.rules import (
    TextRule,
    TrueRule,
    FalseRule,
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
from modules.rp import Rp
from modules.nicknames import Nicknames
from modules.middlewares import Middleware
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
middleware = Middleware(_db, bot.methods, assocs)
rps = Rp(_db, bot.methods)
nicknames = Nicknames(_db)
dorky_trigger = DorkyTrigger()
hello_trigger = HelloTrigger()
morning_trigger = MorningTrigger()
sleep_trigger = SleepTrigger()
twiml = TwiML()


''' ---------MIDDLEWARES--------- '''

@bot.middleware.pre
async def pre_middleware_handler(event: dict):
    return await middleware.prepare_event(event)


''' ---------REGISTRATION--------- '''

@bot.on_event.message_new(FromUser() & ~IsUserRegistered())
async def reg_user(event: dict):
    await bot_users.reg_user(event)

@bot.on_event.message_new(TextRule(value=["$darky reg"], ignore_case=True) & 
                          FromChat() & IsAdminRule() & (AdminRule() | IsBotAdmin()))
async def reg_chat(event: dict):
    return await bot_chats.reg_chat(event)

@bot.on_event.message_new(FromChat() & IsAdminRule() & IsChatRegistered())
async def reg_chat_member(event: dict):
    await bot_chats.reg_chat_member(event)


''' ---------USER SETTINGS--------- '''

@bot.on_event.message_new(TextRule(value=["$darky user settings"], ignore_case=True) & 
                          FromUser())
async def show_user_settings(event: dict):
    return await bot_users.get_user(event)

@bot.on_event.message_new(TwiMLRule(value=["$darky user set <key:word> = <value:word>", "$darky user set <key:word>"], ignore_case=True) & 
                          FromUser())
async def update_user_settings(event: dict, key: str = None, value: str = None):
    return await bot_users.update_user(event, key, value)


''' ---------CHAT SETTINGS--------- '''

@bot.on_event.message_new(TextRule(value=["$darky chat settings"], ignore_case=True) & 
                          FromChat() & FromUser() & IsChatRegistered() & (AdminRule() | IsBotAdmin()))
async def show_chat_settings(event: dict):
    return await bot_chats.show_chat(event)

@bot.on_event.message_new(((TwiMLRule(value=["$darky stats <id>"], ignore_case=True) & MentionRule()) | 
                           (TextRule(value=["$darky stats"], ignore_case=True) & (ReplyRule() | ForwardRule()))) &
                          FromChat() & FromUser() & IsChatRegistered())
async def show_chat_member_stats(event: dict, id: str = None, mentions: dict = None, have_reply: bool = None, have_forward: bool = None):
    member_id = (-mentions[0]["id"] if mentions[0]["type"] == "club" else mentions[0]["id"]) if mentions is not None and len(mentions) > 0 else False
    return await bot_chats.show_chat_member(event, member_id or extractor.extract_userid_from_reply(event, have_reply, have_forward))

@bot.on_event.message_new(TwiMLRule(value=["$darky chat set <key:word> = <value>", "$darky chat set <key:word>"], ignore_case=True) & 
                          FromChat() & FromUser() & IsChatRegistered() & (AdminRule() | IsBotAdmin()))
async def update_chat_settings(event: dict, key: str = None, value: str = None):
    return await bot_chats.update_chat(event, key, value)


''' ---------ON EVERY MESSAGE EVENTS--------- '''

@bot.on_event.message_new(FromChat() & ((IsChatRegistered() & CheckChatSettings(key = "random_messages", value = True)) | TrueRule()))
async def random_speak_handler(event: dict):
    return await witless.generate(event, size = "small")

@bot.on_event.message_new(FromChat() & IsChatRegistered() & 
                          CheckChatSettings(key = "rp", value = True) & 
                          CheckChatSettings(key = "random_rp", value = True))
async def random_rp_handler(event: dict):
    return await rps.random_rp(event)

@bot.on_event.message_new(FromChat() & IsChatRegistered())
async def update_chat_timestamp(event: dict):
    await bot_chats.update_timestamp(event)

@bot.on_event.message_new(FromChat() & IsChatRegistered() & FromUser())
async def update_member_stats(event: dict):
    await bot_chats.update_member_stats(event)
    await bot_chats.note_activity(event)

@bot.on_event.message_new(FromUser())
async def update_user_timestamp(event: dict):
    await bot_users.update_timestamp(event)

@bot.on_event.message_new()
async def requests_handled_increment(event: dict):
    await _db.add_request_handled()


''' ---------NICKNAMES--------- '''

@bot.on_event.message_new(TwiMLRule(value=["$darky nickname <nickname>"]) & 
                          ~TextRule(value=["$darky nickname reset"]) & 
                          ~TwiMLRule(value=["$darky nickname <id> = <nickname>"]) & 
                          ~ReplyRule() & ~ForwardRule() & 
                          FromChat() & FromUser() & IsChatRegistered() & CheckChatSettings(key = "nicknames", value = True))
async def nickname_set_handler(event: dict, nickname: str = None):
    return await nicknames.set(event, None, nickname)

@bot.on_event.message_new(TextRule(value=["$darky nickname reset"]) & 
                          ~ReplyRule() & ~ForwardRule() & ~MentionRule() & 
                          FromChat() & FromUser() & IsChatRegistered() & CheckChatSettings(key = "nicknames", value = True))
async def nickname_reset_handler(event: dict):
    return await nicknames.delete(event, None)

#TODO: changing other's nicknames
@bot.on_event.message_new(((TwiMLRule(value=["$darky nickname <id> = <nickname>"]) & MentionRule()) | 
                           (TwiMLRule(value=["$darky nickname <nickname>"]) & 
                            ~TextRule(value=["$darky nickname reset"]) & (ReplyRule() | ForwardRule()))) & 
                          FromChat() & FromUser() & IsChatRegistered() & CheckChatSettings(key = "nicknames", value = True) & 
                          ((CheckChatSettings(key = "manage_nicknames", value = "all")) | 
                           (CheckChatSettings(key = "manage_nicknames", value = "admins") & (AdminRule() | IsBotAdmin())) | 
                           (CheckChatSettings(key = "manage_nicknames", value = "nobody") & FalseRule())))
async def nickname_set_to_other_handler(event: dict, nickname: str = None, id: str = None, mentions: dict = None, have_reply: bool = None, have_forward: bool = None):
    member_id = (-mentions[0]["id"] if mentions[0]["type"] == "club" else mentions[0]["id"]) if mentions is not None and len(mentions) > 0 else False
    return await nicknames.set(event, member_id or extractor.extract_userid_from_reply(event, have_reply, have_forward), nickname)

@bot.on_event.message_new(((TwiMLRule(value=["$darky nickname reset <id>"]) & MentionRule()) | 
                           (TextRule(value=["$darky nickname reset"]) & (ReplyRule() | ForwardRule()))) & 
                          FromChat() & FromUser() & IsChatRegistered() & CheckChatSettings(key = "nicknames", value = True) & 
                          ((CheckChatSettings(key = "manage_nicknames", value = "all")) | 
                           (CheckChatSettings(key = "manage_nicknames", value = "admins") & (AdminRule() | IsBotAdmin())) | 
                           (CheckChatSettings(key = "manage_nicknames", value = "nobody") & FalseRule())))
async def nickname_set_to_other_handler(event: dict, nickname: str = None, id: str = None, mentions: dict = None, have_reply: bool = None, have_forward: bool = None):
    member_id = (-mentions[0]["id"] if mentions[0]["type"] == "club" else mentions[0]["id"]) if mentions is not None and len(mentions) > 0 else False
    return await nicknames.delete(event, member_id or extractor.extract_userid_from_reply(event, have_reply, have_forward))


''' ---------RP--------- '''

@bot.on_event.message_new(((TwiMLRule(value=["<rp> <id>"], ignore_case=True) & MentionRule()) | 
                           (TwiMLRule(value=["<rp>"], ignore_case=True) & (ReplyRule() | ForwardRule()))) &
                          FromChat() & FromUser() & IsChatRegistered() & CheckChatSettings(key = "rp", value = True))
async def rp_handler(event: dict, rp: str = None, id: str = None, mentions: dict = None, have_reply: bool = None, have_forward: bool = None):
    member_id = (-mentions[0]["id"] if mentions[0]["type"] == "club" else mentions[0]["id"]) if mentions is not None and len(mentions) > 0 else False
    return await rps.do(event["object"]["message"]["peer_id"],
                        event["object"]["message"]["from_id"],
                        rp,
                        member_id or extractor.extract_userid_from_reply(event, have_reply, have_forward))

@bot.on_event.message_new((TextRule(value=["$darky rp list"], ignore_case=True) | 
                           TwiMLRule(value=["$darky rp list <page:int>"], ignore_case=True)) &
                          FromChat() & FromUser() & IsChatRegistered() & CheckChatSettings(key = "rp", value = True))
async def rp_add_handler(event: dict, page: int = 1):
    return await rps.show(event, page)

@bot.on_event.message_new(TwiMLRule(value=["$darky rp <trigger> = [<male_reply>|<female_reply>]"], ignore_case=True) &
                          FromChat() & FromUser() & IsChatRegistered() & CheckChatSettings(key = "rp", value = True) & 
                          ((CheckChatSettings(key = "manage_rp", value = "all")) | 
                           (CheckChatSettings(key = "manage_rp", value = "admins") & (AdminRule() | IsBotAdmin())) | 
                           (CheckChatSettings(key = "manage_rp", value = "nobody") & FalseRule())))
async def rp_add_handler(event: dict, trigger: str = None, male_reply: str = None, female_reply: str = None):
    return await rps.add(event, trigger, male_reply, female_reply)

@bot.on_event.message_new(TwiMLRule(value=["$darky rp del <trigger>"], ignore_case=True) &
                          FromChat() & FromUser() & IsChatRegistered() & CheckChatSettings(key = "rp", value = True) & 
                          ((CheckChatSettings(key = "manage_rp", value = "all")) | 
                           (CheckChatSettings(key = "manage_rp", value = "admins") & (AdminRule() | IsBotAdmin())) | 
                           (CheckChatSettings(key = "manage_rp", value = "nobody") & FalseRule())))
async def rp_add_handler(event: dict, trigger: str = None):
    return await rps.delete(event, trigger)


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

@bot.on_event.message_new((TextRule(value=["$darky top"], ignore_case=True) | TwiMLRule(value=["$darky top <limit:int>"], ignore_case=True)) & 
                          FromChat() & FromUser() & IsChatRegistered())
async def top_handler(event: dict, limit: int = 5):
    return await bot_chats.get_chat_top(event, limit)


''' ---------TRIGGERS--------- '''

@bot.on_event.message_new(ContainsRule(triggers = ["дурки", "дорки", "дорке", "дуркя", "dorky", "doorky", "dorke", "doorke"], ignore_case = True, need_list = False) &
                          (~FromChat() | (FromChat() & (~IsChatRegistered() | IsChatRegistered() & CheckChatSettings(key = "triggers", value = True)))))
async def trigger1(event: dict):
    return dorky_trigger.react()

@bot.on_event.message_new(ContainsRule(triggers = ['прив', 'привет', 'приветствую', 'здравствуйте', 'преет', 'преть', 'приветик', 'приветики', 'здрасте', 'хай', 'хелло', 'добрый день', 'добрый вечер'], ignore_case = True, need_list = False) &
                          (~FromChat() | (FromChat() & (~IsChatRegistered() | IsChatRegistered() & CheckChatSettings(key = "triggers", value = True)))))
async def trigger2(event: dict):
    return hello_trigger.react()

@bot.on_event.message_new(ContainsRule(triggers = ['утра', 'утречка', 'утро', 'доброе утро', 'проснулся', 'проснулась', 'добре', 'проснувся', 'проснувась', 'поспал', 'спал'], ignore_case = True, need_list = False) &
                          (~FromChat() | (FromChat() & (~IsChatRegistered() | IsChatRegistered() & CheckChatSettings(key = "triggers", value = True)))))
async def trigger3(event: dict):
    return morning_trigger.react()

@bot.on_event.message_new(ContainsRule(triggers = ['спокойной', 'ночи', 'споки', 'споке', 'ночки', 'снов', 'спать', 'посплю'], ignore_case = True, need_list = False) &
                          (~FromChat() | (FromChat() & (~IsChatRegistered() | IsChatRegistered() & CheckChatSettings(key = "triggers", value = True)))))
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
                          (~FromChat() | (FromChat() & (~IsChatRegistered() | IsChatRegistered() & CheckChatSettings(key = "layout_autodetect", value = True)))))
async def autocorrection_layout(event: dict, changed_layout: str = None):
    return f"🧐 Возможно вы использовали неправильную раскладку клавиатуры\nЯ исправила текст за вас.\n\nИзмененный текст:\n{changed_layout}"

@bot.on_event.message_new(TextRule(value=["$darky layout"], ignore_case = True) & (ReplyRule() | ForwardRule()))
@bot.on_event.message_new(TwiMLRule(value=["$darky layout <text>"], ignore_case = True))
async def change_layout_text(event: dict, text: str = None, have_reply: bool = None, have_forward: bool = None):
    return await SimpleCommands.layout(text or extractor.extract_text_from_reply(event, have_reply, have_forward))


''' ---------ASSOCS--------- '''

@bot.on_event.message_new(TwiMLRule(value=["$darky assoc <command> = <assoc>"], ignore_case = True) & 
                          FromChat() & FromUser() & IsChatRegistered() & (AdminRule() | IsBotAdmin()))
async def assoc_add_handler(event: dict, command: str = None, assoc: str = None):
    return await assocs.add(event, command, assoc)

@bot.on_event.message_new(TwiMLRule(value=["$darky assoc del <assoc>"], ignore_case = True) &
                          FromChat() & FromUser() & IsChatRegistered() & (AdminRule() | IsBotAdmin()))
async def assoc_del_handler(event: dict, assoc: str = None):
    return await assocs.delete(event, assoc)


''' ---------DARKY-SPEAK--------- '''

@bot.on_event.message_new(TrueRule())
async def speak_handler_push(event: dict):
    await witless.push(event)

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

@bot.on_event.message_new(TextRule(value=["$darky speak wipe"], ignore_case=True) & (AdminRule() | IsBotAdmin()) & FromChat())
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
                  FromChat() & IsAdminRule() & (AdminRule() | IsBotAdmin()))
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
                  FromChat() & IsAdminRule() & (~AdminRule() & ~IsBotAdmin()))
async def access_denied_button(event: dict):
    await bot.methods.messages.sendMessageEventAnswer(event["object"]["event_id"],
                                                      event["object"]["user_id"],
                                                      event["object"]["peer_id"])
    return Replies.ACCESS_DENIED[0], Replies.ACCESS_DENIED[2]


''' ---------WRONG USE COMMANDS--------- '''

# TODO: correct rules for darky chat set etc
@bot.on_event.message_new(TextRule(value=["$darky try", "$darky choose", "$darky guess"], ignore_case=True))
@bot.on_event.message_new((TextRule(value=["$darky chat set", "$darky user set"], ignore_case=True) |
                           TwiMLRule(value = ["$darky chat set <params>", "$darky user set <params>"], ignore_case=True)) &
                          ~TwiMLRule(value=["$darky chat set <key> = <value>", 
                                            "$darky chat set <key>", 
                                            "$darky user set <key> = <value>", 
                                            "$darky user set <key>"], ignore_case=True))
@bot.on_event.message_new((TextRule(value=["$darky assoc", "$darky assoc del"], ignore_case=True) | 
                           TwiMLRule(value=["$darky assoc <params>"], ignore_case=True)) & 
                           ~TwiMLRule(value=["$darky assoc <command> = <assoc>", 
                                             "$darky assoc del <assoc>"], ignore_case=True))
@bot.on_event.message_new(((TwiMLRule(value=["$darky stats <id>"], ignore_case=True)) & ~MentionRule(need_list=False)) |
                           (TextRule(value=["$darky stats"], ignore_case=True) & ~ReplyRule() & ~ForwardRule()))
@bot.on_event.message_new(TwiMLRule(value=["$darky rp <params>"], ignore_case=True) & 
                          ~TwiMLRule(value=["$darky rp <trigger> [<male_reply>|<female_reply>]",
                                            "$darky rp del <params>",
                                            "$darky rp delete <params>",
                                            "$darky rp list <page:int>"], ignore_case=True) & 
                          ~TextRule(value=["$darky rp list"], ignore_case=True))
@bot.on_event.message_new(TwiMLRule(value=["$darky top <params>"], ignore_case=True) & 
                          ~TwiMLRule(value=["$darky top <limit:int>"], ignore_case=True))
@bot.on_event.message_new(TextRule(value=["$darky nickname"], ignore_case=True))
async def wrong_usage_handle(event: dict, **kwargs):
    return Replies.WRONG_USAGE[0], Replies.WRONG_USAGE[2]

@bot.on_event.message_new(TextRule(value=["$darky reg", 
                                          "$darky chat settings"], ignore_case=True) & ~FromChat())
@bot.on_event.message_new(TwiMLRule(value=["$darky chat set <params>",
                                           "$darky assoc <params>"], ignore_case=True) & ~FromChat())
@bot.on_event.message_new((((TwiMLRule(value=["$darky stats <id>"], ignore_case=True)) & ~MentionRule(need_list=False)) |
                           (TextRule(value=["$darky stats"], ignore_case=True) & ~ReplyRule() & ~ForwardRule())) & 
                           ~FromChat())
@bot.on_event.message_new((TwiMLRule(value=["$darky rp <params>"], ignore_case=True)) & 
                          ~FromChat())
@bot.on_event.message_new((TwiMLRule(value=["$darky top <params>"], ignore_case=True)) & 
                          ~FromChat())
@bot.on_event.message_new(TwiMLRule(value=["$darky nickname <params>"], ignore_case=True) & 
                          ~FromChat())
async def not_from_chat_handle(event: dict, **kwargs):
    return Replies.NOT_WORK_HERE[0], Replies.NOT_WORK_HERE[2]

@bot.on_event.message_new(TextRule(value=["$darky chat settings"], ignore_case=True) & 
                          FromChat() & ~IsChatRegistered())
@bot.on_event.message_new(TwiMLRule(value=["$darky chat set <params>",
                                           "$darky assoc <params>"], ignore_case=True) & 
                          FromChat() & ~IsChatRegistered())
@bot.on_event.message_new((((TwiMLRule(value=["$darky stats <id>"], ignore_case=True)) & ~MentionRule(need_list=False)) |
                           (TextRule(value=["$darky stats"], ignore_case=True) & ~ReplyRule() & ~ForwardRule())) & 
                           FromChat() & ~IsChatRegistered())
@bot.on_event.message_new((TwiMLRule(value=["$darky rp <params>"], ignore_case=True)) & 
                          FromChat() & ~IsChatRegistered())
@bot.on_event.message_new((TwiMLRule(value=["$darky top <params>"], ignore_case=True)) & 
                          FromChat() & ~IsChatRegistered())
@bot.on_event.message_new(TwiMLRule(value=["$darky nickname <params>"], ignore_case=True) & 
                          FromChat() & ~IsChatRegistered())
async def not_registered_chat_handle(event: dict, **kwargs):
    return Replies.CHAT_IS_NOT_REGISTERED[0], Replies.CHAT_IS_NOT_REGISTERED[2]

@bot.on_event.message_new(TextRule(value=["$darky reg",
                                          "$darky chat settings"], ignore_case=True) & 
                          FromChat() & ~IsAdminRule())
@bot.on_event.message_new(TwiMLRule(value=["$darky chat set <params>"], ignore_case=True) & 
                          FromChat() & ~IsAdminRule())
@bot.on_event.message_new((((TwiMLRule(value=["$darky stats <id>"], ignore_case=True)) & ~MentionRule(need_list=False)) |
                           (TextRule(value=["$darky stats"], ignore_case=True) & ~ReplyRule() & ~ForwardRule())) & 
                           FromChat() & ~IsAdminRule())
async def bot_is_not_admin_reply(event: dict, **kwargs):
    return Replies.BOT_IS_NOT_ADMIN[0], Replies.BOT_IS_NOT_ADMIN[2]

@bot.on_event.message_new(TextRule(value=["$darky reg",
                                          "$darky chat settings"], ignore_case=True) &
                          FromChat() & (~AdminRule() & ~IsBotAdmin()))
@bot.on_event.message_new(TwiMLRule(value=["$darky chat set <params>",
                                           "$darky assoc <params>"], ignore_case=True) &
                          FromChat() & (~AdminRule() & ~IsBotAdmin()))
@bot.on_event.message_new((TextRule(value=["$darky layout"], ignore_case=True) & (ReplyRule() | ForwardRule()) | 
                           TwiMLRule(value=["$darky layout <params>"], ignore_case=True)) & 
                           FromChat() & (~AdminRule() & ~IsBotAdmin()))
@bot.on_event.message_new((TwiMLRule(value=["$darky rp <params>"], ignore_case=True)) & 
                          FromChat() & IsChatRegistered() & CheckChatSettings(key="manage_rp", value="admins") & (~AdminRule() & ~IsBotAdmin()))
async def access_denied_reply(event: dict, **kwargs):
    return Replies.ACCESS_DENIED[0], Replies.ACCESS_DENIED[2]

@bot.on_event.message_new((TwiMLRule(value=["$darky rp <params>"], ignore_case=True)) & 
                          FromChat() & FromUser() & IsChatRegistered() & 
                          (CheckChatSettings(key = "rp", value = False) | CheckChatSettings(key = "manage_rp", value = "nobody")))
@bot.on_event.message_new(TwiMLRule(value=["$darky nickname <params>"], ignore_case=True) & 
                          ~TwiMLRule(value=["$darky nickname <id> = <nickname>"], ignore_case=True) & 
                          FromChat() & FromUser() & IsChatRegistered() & 
                          CheckChatSettings(key = "nicknames", value = False))
@bot.on_event.message_new(((TwiMLRule(value=["$darky nickname <id> = <nickname>"]) & MentionRule()) | 
                           (TwiMLRule(value=["$darky nickname <nickname>"]) & 
                            ~TextRule(value=["$darky nickname reset"]) & (ReplyRule() | ForwardRule()))) & 
                          FromChat() & FromUser() & IsChatRegistered() & 
                          CheckChatSettings(key = "manage_nicknames", value = "nobody"))
async def disabled_by_admin_reply(event: dict, **kwargs):
    return Replies.DISABLED_BY_ADMIN[0], Replies.DISABLED_BY_ADMIN[2]

bot.start()