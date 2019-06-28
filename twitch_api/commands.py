import sys
import asyncio
from datetime import datetime, date, timedelta
import asyncore, socket, ssl
import requests
from ids import *
from const import *


def is_admin(func):
    def check(*args, **kwargs):
        try:
            msg = args[1]
        except:
            raise Exception("Invalid arguments on bot command")
        if msg.author in owners_list:
            return func(*args, **kwargs)
    return check

async def ping(bot, message):
    await bot.sendmsg("Pong")

async def links(bot, message):
    await bot.sendmsg(LINKS)

@is_admin
async def stop(bot, message):
    if not message.args:
        await bot.stop()


Commands = {
    "ping": ping,
    "links": links,
    "stop": stop
}
