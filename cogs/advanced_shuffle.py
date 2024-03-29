from re import S
import discord
from discord.ext import commands, tasks, vbu

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
        if not isinstance(kahoot_game, KahootGame):
            return await self.restart_task(channel_id, kahoots)

        # Play the game
        await kahoot_game.play_game()

        # Send the final message
        final_message = kahoot_game.get_final_message()
        await channel.send(final_message)

        # Remove the lock
        if channel.id in KahootGame.get_sessions():
            KahootGame.remove_session(channel.id)

        await self.restart_task(channel_id, kahoots)

    async def restart_task(self, channel_id, kahoots):
        await asyncio.sleep(self.MINUTE_DELAY * 60)
        await self.kahoot_task(channel_id, kahoots)

    @vbu.Cog.listener()
    async def on_ready(self):
        async with self.bot.database() as db:
            activated_rows = await db("SELECT channel_id FROM frenzy_activated WHERE activated = $1", True)

        self.activated_channels = set([i['channel_id'] for i in activated_rows])

        for channel_id in self.activated_channels:
            curr_kahoots = await self.get_from_db(channel_id, only_id=True)
            await self.kahoot_task(channel_id, curr_kahoots)

    @commands.command(aliases=['start', 'begin'], application_command_meta=commands.ApplicationCommandMeta())
    @commands.has_permissions(manage_guild=True)
    async def beginfrenzy(self, ctx: vbu.Context):
        """
        Start playing in Frenzy Mode in the current channel
        """
        channel_id = ctx.channel.id

        # Check if we're already Frenzied
        if channel_id in self.activated_channels:
            return await ctx.send("Frenzy Mode is already activated in this channel!")

        # Activate frenzy mode
        async with self.bot.database() as db:
            activated_rows = await db("SELECT channel_id FROM frenzy_activated")
            if channel_id in [i['channel_id'] for i in activated_rows]:
                await db("UPDATE frenzy_activated SET activated = $2 WHERE channel_id = $1", channel_id, True)
            else:
                await db("INSERT INTO frenzy_activated (channel_id, activated) VALUES ($1, $2)", channel_id, True)
        self.activated_channels.add(channel_id)

        # Start frenzying
        kahoots = await self.get_from_db(channel_id, only_id=True)

        # If we don't have any kahoots, we can't play
        if not kahoots:
            return await ctx.send("No Kahoots have been added to this channel! Run the `add` command to add some!")

        # Send a message
        await ctx.send("Frenzy Mode has been activated in this channel! Check the list by running the `list` command")

        # Start the task
        await self.kahoot_task(channel_id, kahoots)

    @commands.command(aliases=['stop'], application_command_meta=commands.ApplicationCommandMeta())
    @commands.has_permissions(manage_guild=True)
    async def endfrenzy(self, ctx: vbu.Context):
        """
        Stop playing in Frenzy Mode in the current channel
        """
        channel_id = ctx.channel.id

        # Make sure we've been activated
        if channel_id not in self.activated_channels:
            return await ctx.send("Frenzy Mode is not activated in this channel!")

        # Deactivate frenzy mode
        async with self.bot.database() as db:
            activated_rows = await db("SELECT channel_id FROM frenzy_activated")
            if channel_id in [i['channel_id'] for i in activated_rows]:
                await db("UPDATE frenzy_activated SET activated = $2 WHERE channel_id = $1", channel_id, False)
            else:
                await db("INSERT INTO frenzy_activated (channel_id, activated) VALUES ($1, $2)", channel_id, False)
        self.activated_channels.remove(channel_id)

        # Send a message
        await ctx.send("Ending Frenzy-Mode after the current game has ended!")

    @commands.command(aliases=['addids', 'addid'], application_command_meta=commands.ApplicationCommandMeta())
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

    @commands.command(aliases=['removeids', 'removeid'], application_command_meta=commands.ApplicationCommandMeta())
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

    @commands.command(application_command_meta=commands.ApplicationCommandMeta())
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

    @commands.command(aliases=['getid', 'getids', "listids", "listid"], application_command_meta=commands.ApplicationCommandMeta())
    @commands.has_permissions(manage_guild=True)
    async def list(self, ctx: vbu.Context, names_only = False):
        """
        Sends the current list of "name: id" pairs. Set names_only to 1 to only get the names
        """

        curr_pairs = await self.get_from_db(ctx.channel.id)

        identifier = "__Name__" if names_only else "__Name: ID__"
        formatted_list = self.get_formatted_message(curr_pairs, names_only)
        await ctx.send(identifier + formatted_list)


    async def get_from_db(self, channel_id, only_id=False):
        async with self.bot.database() as db:
            curr_pairs = await db("SELECT * FROM name_id_pairs WHERE channel_id = $1", channel_id)
            if only_id:
                curr_pairs = [i['id'] for i in curr_pairs]
            return curr_pairs

    @commands.command(aliases=['activatedchannels'], application_command_meta=commands.ApplicationCommandMeta())
    @commands.is_owner()
    async def activated(self, ctx: vbu.Context):
        """
        Sends a list of all the channels that are currently activated
        """
        if not self.activated_channels:
            return await ctx.send("No channels are currently activated!")

        formatted_list = [self.bot.get_channel(i).mention for i in self.activated_channels]
        await ctx.send(f"Activated Channels:\n{' '.join(formatted_list)}")

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
