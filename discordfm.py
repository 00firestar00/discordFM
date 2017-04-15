import configparser
import os
import signal
import sys
from pprint import pprint

import asyncio
import discord
import pylast
from discord.ext import commands
from discord.ext.commands import Bot


class DiscordFM(Bot):
    _current_track = ""

    def __init__(self, conf,
                 command_prefix=commands.when_mentioned_or("#!"),
                 formatter=None,
                 name="DiscordFM",
                 description="""Sets your status to what's playing on LastFM""",
                 pm_help=False, **options):
        super().__init__(command_prefix, formatter, description, pm_help, **options)

        self.config = conf
        self.name = name

        if not sys.platform.startswith('win'):  # pragma: no cover
            self.loop.add_signal_handler(getattr(signal, "SIGTERM"), self.exit)

    async def on_ready(self):
        print("-"*48)
        print("Logged in as")
        print(self.user.name)
        print(self.user.id)
        print("-"*48)

        apikey = config.get("LastFM", "apikey", fallback=None)
        user = config.get("LastFM", "user", fallback=None)

        if apikey is None:
            print("Error: Non LastFM API Key specified")

        if user is None:
            print("Error: Non LastFM user specified")

        lastfm = pylast.LastFMNetwork(
            api_key=apikey
        )

        await self.change_presence(game=discord.Game(name="DiscordFM"))

        while True:
            current_track = lastfm.get_user(user).get_now_playing()
            await self.set_now_playing(current_track)
            await asyncio.sleep(5)

    async def set_now_playing(self, track: pylast.Track):
        if track is None:
            return
        new_track = "{} - {}".format(track.get_artist().get_name(), track.get_name())
        if new_track != self._current_track:
            self._current_track = new_track
            print("Now playing: {}".format(self._current_track))
            await self.change_presence(game=discord.Game(name="{}".format(self._current_track)))

    async def on_command_error(self, exception, ctx):
        pprint(exception)

    async def close(self):
        print("Closing client...")
        await self.change_presence(game=None)
        await super().close()

    @staticmethod
    def exit():
        # This gets handled in the run() method
        raise KeyboardInterrupt


config = configparser.RawConfigParser()
config_file = os.path.dirname(os.path.realpath(__file__)) + "/config.ini"
config.read(config_file)

if not config.has_section("Discord") or not config.has_section("LastFM"):
    print("Error: Config file is invalid.")
    quit()

token = config.get("Discord", "token", fallback=None)

if token is None or "XXXXX" in token:
    username = config.get("Discord", "user", fallback=None)
    password = config.get("Discord", "pass", fallback=None)
    if username is None or password is None:
        print("Error: You need to specify a token, or username and password")
        quit()

    DiscordFM(config).run(username, password)
else:
    DiscordFM(config).run(token, bot=False)
