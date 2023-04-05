import asyncio

from telethon import TelegramClient, events
from telethon.tl.types import Message

from settings import *

############## Client Setup ###############

client = TelegramClient(None, 6, "eb06d4abfb49dc3eeb1aeb98ae0f581e")
loop = asyncio.get_event_loop()


async def start_bot(token: str) -> None:
    await client.start(bot_token=token)
    client.me = await client.get_me()
    print(client.me.username, "is Online Now.")


loop.run_until_complete(start_bot(BOT_TOKEN))

############## Funcs ###############


def get_chat(text: str, rec=False) -> str:
    if "@" in text:
        return text.split()[0]
    if "/" in text:
        if text.split("/")[-1].strip().isdigit():
            return get_chat(text.split("/")[-2], rec=True), int(text.split("/")[-1])
        return text.split("/")[-1]
    try:
        return int(text.strip())
    except BaseException:
        if rec:
            return text
        return ""


def get_number(text: str) -> int:
    if "all" in text.lower():
        return 0
    try:
        return int(text)
    except BaseException:
        return False


def get_chats(text: str) -> list:
    return [get_chat(z) for z in text.split() if z]


async def main_task(
    e: events.NewMessage.Event,
    source_chat: str,
    posts: int,
    views: int,
    last: int,
    dests: list,
) -> None:
    if not (source_chat and views and last and dests):
        return
    r, v, f = 0, 0, 0
    for z in reversed(range(posts, last)):
        try:
            msg = await client.get_messages(source_chat, ids=[z])
            if isinstance(msg, list):
                msg = msg[0]
            if not msg:
                continue
            r += 1
            if not isinstance(msg, Message) or not msg.views < views:
                continue
            v += 1
            for dest in dests:
                try:
                    await msg.forward_to(dest)
                    await asyncio.sleep(35)
                    f += 1
                except BaseException:
                    pass
        except BaseException:
            pass
    await client.send_message(
        e.sender_id,
        f"Total Checked: {r} Posts\nLess Views on: {v} Posts\nTotal Forwards: {f}",
    )


############## Event Handlers ###############


@client.on(events.NewMessage(incoming=True, pattern="\\/start"))
async def on_start(e: events.NewMessage.Event) -> None:
    await e.reply("Hello.")


@client.on(events.NewMessage(incoming=True, pattern="\\/check"))
async def do_task(e: events.NewMessage.Event) -> None:
    if e.sender_id in ADMINS:
        async with client.conversation(e.sender_id, timeout=20000000) as conv:
            await conv.send_message(
                "Forward the last post of source channel \n\nmake sure bot must be admin there"
            )
            res = await conv.get_response()
            chat, lid = res.fwd_from.from_id.channel_id, res.fwd_from.channel_post
            await conv.send_message(
                "Number of messages to check? \n\nSend 'ALL' for All Post"
            )
            res = await conv.get_response()
            msgs = get_number(res.text)
            await conv.send_message("Send Minimum Views Number")
            res = await conv.get_response()
            views = int(res.text)
            await conv.send_message(
                f"Send Channel UserName or Id to Forward posts. \nIf views less than {views}\nmake sure bot is admin"
            )
            res = await conv.get_response()
            dests = get_chats(res.text)
            await conv.send_message("Process Started, i'll notify when its Complete")
        await main_task(e, chat, msgs, views, lid, dests)


client.run_until_disconnected()
