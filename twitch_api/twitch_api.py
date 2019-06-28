import sys
import asyncio, aiohttp, json, asyncpg
from aiohttp import ClientSession
from datetime import datetime, date, timedelta
import asyncore, socket, ssl
import requests



class Message:
    def __init__(self, msg: str=""):
        self.author = ""
        self.channel = ""
        self.content = ""
        self.command = ""
        self.args = ""
        self.type = ""
        self.host = ""
        self.created_at = datetime.utcnow()

        self._specials = msg.split(":", 1)[0]
        if self._specials:
            try:
                self._specials = self._specials.replace("@", "")
                specs = {}
                for spec in self._specials.split(";"):
                    key, value = spec.split("=", 1)
                    specs[key] = value
                self._specials = specs
            except:
                pass
        msg_ = msg.split(":", 1)[-1]
        msg_ = msg_.split(" ", 2)
        self.host = msg_[0] if len(msg_) > 0 else ""
        self.type = msg_[1].lower() if len(msg_) > 1 else ""
        self._text = msg_[2] if len(msg_) > 2 else ""
        try:
            self.author = self.host.split('!',1)[0].rsplit(":", 1)[-1]
            self.channel = self._text.split(':',1)[0]
            self.content = self._text.split(':',1)[1]
        except Exception as e:
            pass
        if self.content.startswith("!"):
            ctx = self.content.split(" ", maxsplit=1)
            self.command = ctx[0][1:].lower()
            if len(ctx) > 1:
                self.args = ctx[1]

    def __repr__(self):
        return "<Message:\n- host={0.host}\n- type={0.type}\n- text={0._text}\n- author={0.author}\n- channel={0.channel}\n- content={0.content}\n- command={0.command}\n- args={0.args}\n- created_at={0.created_at}\n>".format(self)

    def __str__(self):
        return "<Message:\n- host={0.host}\n- type={0.type}\n- text={0._text}\n- author={0.author}\n- channel={0.channel}\n- content={0.content}\n- command={0.command}\n- args={0.args}\n- created_at={0.created_at}\n>".format(self)

class Bot:
    def __init__(self, *args, **kwargs):
        self.reader = None
        self.writer = None
        self.loop = asyncio.get_event_loop()
        self.server = "irc.chat.twitch.tv"
        self.token = kwargs.get("token", None)
        self.api_token = None
        self.client_id = str(kwargs.get("client_id", None))
        self.client_secret = str(kwargs.get("client_secret", None))
        self.port = 6667
        self.channel = kwargs.get("channel", "#pineapple_cookie_")
        self.nick = kwargs.get("nick", "Tomori")
        self.exitcode = "bye " + self.nick
        self._commands = {}
        self.is_closed = True

    async def run(self):
        await self._connect()
        await self.joinchan(self.channel)
        while not self.is_closed:
          msg = await self.reader.read(2048)
          msg = msg.decode().strip('\n\r')
          for m in msg.split("\r\n"):
              asyncio.ensure_future(self._handle_command(m))

    async def _send(self, com, val):
        self.writer.write("{} {}\n".format(
            com.upper(),
            val).encode()
        )

    async def stop(self):
        await self.sendmsg("cya")
        await self._send("PART", self.channel)
        self.writer.close()
        self.is_closed = True

    async def _connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.server, self.port, loop=self.loop)
        await self._get_api_token()
        await self._send("PASS", "oauth:"+self.token)
        await self._send("NICK", self.nick)
        await asyncio.wait([
            self._send("CAP", "REQ :twitch.tv/tags twitch.tv/membership"),
            self._send("CAP", "REQ :twitch.tv/tags twitch.tv/tags"),
            self._send("CAP", "REQ :twitch.tv/tags twitch.tv/commands")
        ])
        self.is_closed = False

    def event(self, coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('Тип события должен быть корутиной')

        setattr(self, coro.__name__, coro)
        return coro

    def command(*args, **kwargs):
        self = args[0]
        def set_command(coro):
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError("Тип события '%s' должен быть корутиной" % coro.__name__)

            name = str(kwargs.get("name", coro.__name__)).lower()

            if not name in self._commands.keys():
                self._commands[name] = coro
            return coro
        return set_command

    async def _get_api_token(self):
        self.api_token = None
        async with ClientSession() as session:
            async with session.post(
                "https://id.twitch.tv/oauth2/token?client_id={id}&client_secret={secret}&grant_type=client_credentials&scope=chat:read+chat:edit+channel:moderate+viewing_activity_read".format(
                    id=self.client_id,
                    secret=self.client_secret
                )
            ) as response:
                if response.status == 200:
                    resp = await response.json()
                    self.api_token = str(resp.get("access_token"))
                else:
                    raise Exception("Can't get access token")
        return self.api_token

    async def joinchan(self, channel):
        await self._send("JOIN", channel)
        msg = ""


    async def _handle_command(self, msg):
        message = Message(msg)

        if message.type == "join" and hasattr(self, "on_member_join"):
            return await self.on_member_join(message.author, message.channel)
        if message.type == "privmsg" and hasattr(self, "on_message"):
            return await self.on_message(message)

        if message.command in self._commands.keys():
            await self._commands[message.command](self, message)

    async def process_command(self, message):
        if not isinstance(message, Message):
            message = Message(str(message))

        if message.command in self._commands.keys():
            await self._commands[message.command](self, message)

    async def ping(self):
        await self._send("PONG", ":pingis")

    async def sendmsg(self, msg, target=None):
        if not target:
            target = self.channel
        await self._send("PRIVMSG", "{target} :{msg}\n".format(target=target,msg=msg))
