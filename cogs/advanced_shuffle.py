import voxelbotutils as vbu


class AdvancedShuffle(vbu.Cog):

    @vbu.command(aliases=['addids'])
    async def add(self, ctx: vbu.Context, *, pairs: str):
        """
        A (quite advanced) command to add multiple name-ID pairs to a channel at once

        Format:
        /add id name, id2 name2, id3 name3

        Note: Names can't have a comma in them
        """

        pairs = pairs.split(",")

        async with self.bot.database() as db:
            for pair in pairs:
                curr_split = pair.strip().split(" ")
                curr_id = curr_split[0]
                curr_name = " ".join(curr_split[1:])

                try:
                    await db("INSERT INTO name_id_pairs (channel_id, name, id) VALUES ($1, $2, $3)", ctx.channel.id, curr_name, curr_id)
                except:
                    await ctx.send(f"The pair {curr_name} - {curr_id} had one or more repeating values in the database!")

            curr_pairs = await db("SELECT name, id FROM name_id_pairs WHERE channel_id = $1", ctx.channel.id)

        pairs_message = "Interpreted list:\n" + self.get_formatted_message(curr_pairs)

        await ctx.send(pairs_message)

    def get_formatted_message(pairs):
        final_message = "__**Name: ID**__"

        for pair in pairs:
            final_message += f"\n{pair['name']}: {pair['id']}"

        return final_message

def setup(bot: vbu.Bot):
    x = AdvancedShuffle(bot)
    bot.add_cog(x)
