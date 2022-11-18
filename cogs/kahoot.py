from .localutils.kahoot_player import KahootGame
import voxelbotutils as vbu
import cogs.localutils as utils


class KahootCommand(vbu.Cog):

    def __init__(self, bot):
        self.bot = bot

    @vbu.command(aliases=['kahootdata', 'getdata', 'get'])
    async def data(self, ctx: vbu.Context, kahoot: str = None):
        """
        Gets the data for a given kahoot.
        """

        kahoot_id, requester = await utils.setup_kahoot(self.bot, ctx.channel, ctx.author, kahoot)

        if not requester:
            return

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

        embed = vbu.Embed()
        embed.color = 5047956
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

        self.bot.logger.info(f"Data Sent for {kahoot}")

    @vbu.command(aliases=['cancelgame', 'end'])
    async def cancel(self, ctx: vbu.Context, password: str = None):
        """
        Cancels the current kahoot game.
        """
        if not password:
            return await ctx.send("Check your DMs for the Kahoot game's password!")

        if ctx.channel.id not in KahootGame.get_sessions():
            return await ctx.send("There is no Kahoot game in this channel!")

        if password != KahootGame.get_sessions()[ctx.channel.id]:
            return await ctx.send("The password you entered is incorrect!")

        await ctx.send("Cancelling the game.")
        KahootGame.remove_session(ctx.channel.id)

    @vbu.command(aliases=['kahoot', 'quiz'])
    async def play(self, ctx: vbu.Context, kahoot: str = None):
        """
        Plays a quiz
        """
        # Send a confirmation message
        await ctx.send(f"Starting Kahoot game!")

        # Create a game and see if we succeeded
        kahoot_game = await KahootGame.create_game(self.bot, ctx.channel, ctx.author, kahoot)
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

        self.bot.logger.info(f"Kahoot Game played {kahoot}")
        await (self.bot.get_user(322542134546661388)).send(f"Kahoot Game played {kahoot}")



def setup(bot: vbu.Bot):
    x = KahootCommand(bot)
    bot.add_cog(x)
