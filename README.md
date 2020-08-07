# twitch-api
A libriary for twitch bots

this is a sample

```python
import sys
import asyncio, aiohttp, json, asyncpg
from datetime import datetime, date, timedelta

from twitch_api import Bot

token = ""
bot = Bot(token=token)

@bot.event
async def on_channel_join(channel):
    print("[+] Joined channel '%s'" % channel)

@bot.event
async def on_message(message):
    print(message)
    await bot.process_command(message)

async def main():
  await bot.run()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
```
