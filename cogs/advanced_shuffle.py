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
            split = pair.split(" ")
            id = split[0]
            name = " ".join(split[1:])

            if ctx.channel.id in self.temporary_db.keys():
                self.temporary_db[ctx.channel.id] += (id, name)
            else:
                self.temporary_db[ctx.channel.id] = [(id, name)]

        await ctx.send(self.temporary_db)



def setup(bot: vbu.Bot):
    x = AdvancedShuffle(bot)
    bot.add_cog(x)
