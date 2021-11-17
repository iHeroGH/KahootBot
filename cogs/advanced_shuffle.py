import voxelbotutils as vbu


class AdvancedShuffle(vbu.Cog):

    temporary_db = dict()

    @vbu.command(aliases=['addids'])
    async def add(self, ctx: vbu.Context, *, pairs: str):
        """
        A (quite advanced) command to add multiple name-ID pairs to a channel at once

        Format:
        /add id name, id2 name2, id3 name3

        Note: Names can't have a comma in them
        """

        pairs = pairs.split(",")

        for pair in pairs:
            curr_split = pair.split(" ")
            curr_id = curr_split[0]
            curr_name = " ".join(curr_split[1:])

            if ctx.channel.id in self.temporary_db.keys():
                self.temporary_db[ctx.channel.id] += [(curr_id, curr_name)]
            else:
                self.temporary_db[ctx.channel.id] = [(curr_id, curr_name)]

        await ctx.send(self.temporary_db)



def setup(bot: vbu.Bot):
    x = AdvancedShuffle(bot)
    bot.add_cog(x)
