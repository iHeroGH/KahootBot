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
        # Set up all the variables
        title = requester.get_title() # Title of the game
        description = requester.get_description() # Description of the game
        url = utils.get_quiz_link(kahoot_id) # Link to the game
        thumbnail = requester.get_thumbnail() # Cover image of the game
        popularity = requester.get_popularity() # Popularity of the game (Plays/Players/Favorites)
        question_count = requester.get_question_count() # Number of questions in the game
        creator_name, creator_icon = requester.get_creator() # Name and icon of the game creator
        created_at = utils.get_date(requester.get_created_at()) # Date the game was created

        embed = vbu.Embed(use_random_colour=True)
        embed.title = title if title else "No Title" # Embed title
        embed.description = description if description else "No Description" # Embed description
        if url:
            embed.url = url # Users can press the title and be redirected to the quiz link
        if thumbnail:
            embed.set_thumbnail(url=thumbnail) # Set the thumbnail

        # Add the data
        if popularity:
            embed.add_field(name="Popularity", value=popularity) # How many plays/players/favorites the quiz has
        if question_count:
            embed.add_field(name="Questions", value=f"{question_count} questions") # How many questions the quiz has

        # Add the footer
        embed.set_footer(**utils.get_footer_items(creator_name, created_at, creator_icon))

        # And send it
        try:
            await ctx.send(embed=embed)
        except:
            await ctx.send("Something went wrong sending the embed.")
        
def setup(bot: vbu.Bot):
    x = KahootCommand(bot)
    bot.add_cog(x)
