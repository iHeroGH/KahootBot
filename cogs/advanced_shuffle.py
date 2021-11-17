import voxelbotutils as vbu

import cogs.localutils.helper_functions as utils


class AdvancedShuffle(vbu.Cog):

    @vbu.command(aliases=['addids', 'addid'])
    async def add(self, ctx: vbu.Context, *, ids: str):
        """
        A command to add multiple IDs to a channel at once. Enter IDs separated by a space (ID1, ID2, ID3)
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
    async def remove(self, ctx: vbu.Context, *, ids: str):
        """
        A command to remove multiple IDs to a channel at once. Enter IDs separated by a space (ID1, ID2, ID3)
        """
        ids = ids.split(" ")

        async with self.bot.database() as db:
            for id in ids:

                id = utils.find_id(id)
                await db("DELETE FROM name_id_pairs WHERE channel_id = $1 AND id = $2", ctx.channel.id, id)

        await ctx.send("Removed the selected values! Check the list by running the `list` command")

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
        if not pairs:
            return "No pairs have been created!"

        final_message = "__Name: ID__"

        for pair in pairs:
            if not names_only:
                final_message += f"\n**{pair['name']}**: {pair['id']}"
            else:
                final_message += f"\n**{pair['name']}**"

        return final_message

def setup(bot: vbu.Bot):
    x = AdvancedShuffle(bot)
    bot.add_cog(x)
