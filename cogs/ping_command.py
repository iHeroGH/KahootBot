import discord
from discord.ext import commands, vbu

class PingCommand(vbu.Cog):

    @commands.command()
    async def ping(self, ctx: vbu.Context):
        """
        A sexy lil ping command for the bot.
        """

        await ctx.send("Pong!")
    
    @commands.command()
    async def privacy(self, ctx: vbu.Context):
        """
        Sends the bot's privacy info link
        """
        await ctx.send("<https://github.com/iHeroGH/KahootBot/blob/main/privacy_info>")


def setup(bot: vbu.Bot):
    x = PingCommand(bot)
    bot.add_cog(x)
