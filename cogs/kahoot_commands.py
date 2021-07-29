import voxelbotutils as vbu
import localutils as utils

class KahootCommand(vbu.Cog):

    @vbu.command(aliases=['kahootdata', 'getdata', 'get'])
    async def data(self, ctx: vbu.Context, kahoot: str = None):
        """
        Gets the data for a given kahoot.
        """
        
        # Get a message
        if not kahoot:
            await ctx.send("What quiz would you like to play? (Either the link or the long ID)")
            kahoot = await self.bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            kahoot = kahoot.content

        # Make sure we got an ID
        try:
            kahoot_id = utils.find_id(kahoot)
        except TypeError:
            return await ctx.send("I couldn't find a valid ID in your message.")

        # Get the quiz link
        quiz_link = utils.get_data_link(kahoot_id)

        # Get a requester object
        requester = await utils.KahootRequester.get_quiz_data(quiz_link)

        # Make sure the game is valid
        if not requester.is_valid:
            return await ctx.send("No game was found with the given ID.")

        # Create the embed
        embed = vbu.Embed(use_random_colour=True)
        embed.title = f"{requester.get_title()}"
        embed.description = f"{requester.get_description()}"
        embed.url = utils.get_quiz_link(kahoot_id) # Users can press the title and be redirected to the quiz link
        embed.set_thumbnail(url=requester.get_thumbnail())

        # Add the data
        embed.add_field(name="Popularity", value=requester.get_popularity()) # How many plays/players/favorites the quiz has
        embed.add_field(name="Questions", value=f"{requester.get_question_count()} questions") # How many questions the quiz has

        # Add the footer
        creator_name, creator_icon = requester.get_creator() # Get the creator's name and icon
        embed.set_footer(text = f"{creator_name} • Created {utils.get_date(requester.get_created_at())}", icon_url = creator_icon)

        # And send it
        await ctx.send(embed=embed)
        
        
def setup(bot: vbu.Bot):
    x = KahootCommand(bot)
    bot.add_cog(x)
