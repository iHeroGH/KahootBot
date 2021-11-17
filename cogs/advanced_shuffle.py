import voxelbotutils as vbu

from .localutils.requester import KahootRequester
import localutils as utils


class AdvancedShuffle(vbu.Cog):

    @vbu.command(aliases=['addids'])
    async def add(self, ctx: vbu.Context, *, pairs: str):
        """
        A (quite advanced) command to add multiple name-ID pairs to a channel at once

        Format:
        /add name: id, name2: id2, name3: id3

        Note: Names can't have a colon in them
        """

        pairs = pairs.split(",")

        async with self.bot.database() as db:
            added = False
            for pair in pairs:
                curr_split = pair.split(":")
                curr_name = curr_split[0].strip()
                curr_id = curr_split[1].strip()

                if not utils.validate_requester(ctx, curr_id)[1]: # If it ain't valid
                    continue

                try:
                    await db("INSERT INTO name_id_pairs (channel_id, name, id) VALUES ($1, $2, $3)", ctx.channel.id, curr_name, curr_id)
                    added = True
                except:
                    await ctx.send(f"The pair {curr_name}: {curr_id} had one or more repeating values in the database!")

        if added:
            await ctx.send("Added the new values! Check the list by running the `list` command")

    @vbu.command(aliases=['getid', 'getids', "listids", "listid"])
    async def list(self, ctx: vbu.Context, names_only = False):
        """
        Lists the current list of name: id pairs. Set names_only to True to only get the names.
        """

        curr_pairs = await self.get_from_db(ctx)
        await ctx.send(self.get_formatted_message(curr_pairs))

    async def get_from_db(self, ctx):
        async with self.bot.database() as db:
            return await db("SELECT name, id FROM name_id_pairs WHERE channel_id = $1", ctx.channel.id)

    def get_formatted_message(self, pairs = None, names_only = False):
        final_message = "__**Name: ID**__"

        for pair in pairs:
            if not names_only:
                final_message += f"\n{pair['name']}: {pair['id']}"
            else:
                final_message += f"\n{pair['name']}"

        return final_message

def setup(bot: vbu.Bot):
    x = AdvancedShuffle(bot)
    bot.add_cog(x)
