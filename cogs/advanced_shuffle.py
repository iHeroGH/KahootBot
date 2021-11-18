from re import S
import voxelbotutils as vbu
import discord
from discord.ext import commands, tasks

import cogs.localutils.helper_functions as utils
from cogs.localutils.kahoot_player import KahootGame

import random
import asyncio

class AdvancedShuffle(vbu.Cog):

    MINUTE_DELAY = 3
    activated_channels = set()

    async def kahoot_task(self, channel_id, kahoots):

        # If we are still activated
        if channel_id not in self.activated_channels:
            return

        channel = self.bot.get_channel(channel_id)

        # Try creating a game until it works
        kahoot_game = await KahootGame.create_game(self.bot, channel, None, random.choice(kahoots))
        while not isinstance(kahoot_game, KahootGame):
            kahoot_game = await KahootGame.create_game(self.bot, channel, None, random.choice(kahoots))

        # Play the game
        await kahoot_game.play_game(abstract=True)

        # Send the final message
        final_message = kahoot_game.get_final_message()
        await channel.send(final_message)

        # Remove the lock
        if channel.id in KahootGame.get_sessions():
            KahootGame.remove_session(channel.id)

        await asyncio.sleep(self.MINUTE_DELAY * 60)

    @vbu.Cog.listener()
    async def on_ready(self):
        async with self.bot.database() as db:
            activated_rows = await db("SELECT channel_id FROM frenzy_activated WHERE activated = $1", True)

        self.activated_channels = set([i['channel_id'] for i in activated_rows])

        for channel_id in self.activated_channels:
            curr_kahoots = await self.get_from_db(channel_id, only_id=True)
            await self.kahoot_task(channel_id, curr_kahoots)

    @vbu.command(aliases=['start', 'begin'])
    @commands.has_permissions(manage_guild=True)
    async def beginfrenzy(self, ctx: vbu.Context):
        """
        Start playing in Frenzy Mode in the current channel
        """
        channel_id = ctx.channel.id

        async with self.bot.database() as db:
            await db("UPDATE frenzy_activated SET activated = $2 WHERE channel_id = $1", channel_id, True)

        self.activated_channels.add(channel_id)

        kahoots = await self.get_from_db(channel_id, only_id=True)
        await self.kahoot_task(channel_id, kahoots)

        await ctx.send("Frenzy Mode has been activated in this channel!  Check the list by running the `list` command")

    @vbu.command(aliases=['stop'])
    @commands.has_permissions(manage_guild=True)
    async def endfrenzy(self, ctx: vbu.Context):
        """
        Stop playing in Frenzy Mode in the current channel
        """
        channel_id = ctx.channel.id

        async with self.bot.database() as db:
            await db("UPDATE frenzy_activated SET activated = $2 WHERE channel_id = $1", channel_id, False)

        self.activated_channels.remove(channel_id)

        await ctx.send("Ending Frenzy-Mode after the current game has ended!")

    @vbu.command(aliases=['addids', 'addid'])
    @commands.has_permissions(manage_guild=True)
    async def add(self, ctx: vbu.Context, *, ids: str):
        """
        Adds multiple IDs to a channel at once. (ID1 ID2 ID3 etc)
        """
        ids = ids.split(" ")

        async with self.bot.database() as db:
            added = False
            for id in ids:

                if not (req := await utils.validate_requester(ctx, id))[1]: # If it ain't valid
                    continue

                id = req[0]
                curr_name = req[1].get_title()

                try:
                    await db("INSERT INTO name_id_pairs (channel_id, name, id) VALUES ($1, $2, $3)", ctx.channel.id, curr_name, id)
                    added = True
                except:
                    await ctx.send(f"The pair {curr_name}: {id} had one or more repeating values in the database!")

        if added:
            await ctx.send("Added the new values! Check the list by running the `list` command")

    @vbu.command(aliases=['removeids', 'removeid'])
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx: vbu.Context, *, ids: str):
        """
        Removes multiple IDs from a channel at once. (ID1 ID2 ID3 etc)
        """
        ids = ids.split(" ")

        async with self.bot.database() as db:
            for id in ids:

                if not (req := await utils.validate_requester(ctx, id))[1]: # If it ain't valid
                    continue

                id = req[0]

                await db("DELETE FROM name_id_pairs WHERE channel_id = $1 AND id = $2", ctx.channel.id, id)

        await ctx.send("Removed the selected values! Check the list by running the `list` command")

    @vbu.command()
    @commands.has_permissions(manage_guild=True)
    async def removeall(self, ctx: vbu.Context):
        """
        Removes all the IDs from a channel at once
        """
        curr_pairs = await self.get_from_db(ctx.channel.id)
        formatted_message = self.get_formatted_message(curr_pairs)

        async with self.bot.database() as db:
            await db("DELETE FROM name_id_pairs WHERE channel_id = $1", ctx.channel.id)

        await ctx.send(f"Removed:{formatted_message}")

    @vbu.command(aliases=['getid', 'getids', "listids", "listid"])
    @commands.has_permissions(manage_guild=True)
    async def list(self, ctx: vbu.Context, names_only = False):
        """
        Sends the current list of "name: id" pairs.
        """

        curr_pairs = await self.get_from_db(ctx.channel.id)
        await ctx.send("__Name: ID__" + self.get_formatted_message(curr_pairs))


    async def get_from_db(self, channel_id, only_id=False):
        async with self.bot.database() as db:
            curr_pairs = await db("SELECT * FROM name_id_pairs WHERE channel_id = $1", channel_id)
            if only_id:
                curr_pairs = [i['id'] for i in curr_pairs]
            return curr_pairs

    def get_formatted_message(self, pairs = None, names_only = False):
        if not pairs:
            return "\nNo pairs have been created!"

        final_message = ""

        for pair in pairs:
            if not names_only:
                final_message += f"\n**{pair['name']}**: {pair['id']}"
            else:
                final_message += f"\n**{pair['name']}**"

        return final_message

def setup(bot: vbu.Bot):
    x = AdvancedShuffle(bot)
    bot.add_cog(x)
