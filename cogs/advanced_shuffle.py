import voxelbotutils as vbu
from discord.ext import commands, tasks

import cogs.localutils.helper_functions as utils
from cogs.localutils.kahoot_player import KahootGame

import random

class AdvancedShuffle(vbu.Cog):

    @tasks.loop(seconds=3)
    async def kahoot_task(self, ctx: vbu.Context, kahoots):
        current_kahoot = 0

        # Create a game and see if we succeeded
        kahoot_game = await KahootGame.create_game(ctx, kahoots[current_kahoot])
        if not isinstance(kahoot_game, KahootGame):
            return

        # Play the game
        await kahoot_game.play_game()

        # Send the final message
        final_message = kahoot_game.get_final_message()
        await ctx.send(final_message)

        # Remove the lock
        if ctx.channel.id in KahootGame.get_sessions():
            return KahootGame.remove_session(ctx.channel.id)

        current_kahoot += 1

    @vbu.command(aliases=['start', 'begin'])
    @commands.has_permissions(manage_guild=True)
    async def beginfrenzy(self, ctx: vbu.Context):
        """
        Start playing in Frenzy Mode in the current channel
        """
        kahoots = [i['id'] for i in await self.get_from_db(ctx.channel.id)]
        random.shuffle(kahoots)

        await ctx.send("Frenzy Mode has been activated in this channel!  Check the list by running the `list` command")
        self.kahoot_task.start(ctx, kahoots)

    @vbu.command(aliases=['stop'])
    @commands.has_permissions(manage_guild=True)
    async def endfrenzy(self, ctx: vbu.Context):
        """
        Stop playing in Frenzy Mode in the current channel
        """
        await ctx.send("Ending Frenzy-Mode after the current game has ended!")
        self.kahoot_task.stop()

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


    async def get_from_db(self, channel_id):
        async with self.bot.database() as db:
            return await db("SELECT name, id FROM name_id_pairs WHERE channel_id = $1", channel_id)

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
