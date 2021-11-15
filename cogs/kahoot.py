from localutils.helper_functions import disable_components
from localutils.kahoot_player import KahootGame
import voxelbotutils as vbu
import localutils as utils

import discord

import asyncio
import random

class KahootCommand(vbu.Cog):

    def __init__(self, bot):
        self.bot = bot

    @vbu.command(aliases=['kahootdata', 'getdata', 'get'])
    async def data(self, ctx: vbu.Context, kahoot: str = None):
        """
        Gets the data for a given kahoot.
        """

        kahoot_id, requester = await utils.setup_kahoot(ctx, kahoot)

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

    @vbu.command(aliases=['cancelgame', 'end'])
    async def cancel(self, ctx: vbu.Context, password: str = None):
        """
        Cancels the current kahoot game.
        """
        if not password:
            return await ctx.send("Check your DMs for the Kahoot game's password!")

        if ctx.channel.id not in self.kahoot_sessions.keys():
            return await ctx.send("There is no Kahoot game in this channel!")

        if password != self.kahoot_sessions[ctx.channel.id]:
            return await ctx.send("The password you entered is incorrect!")

        await ctx.send("Cancelling the game.")
        KahootGame.remove_session(ctx.channel.id)

    @vbu.command(aliases=['kahoot', 'quiz'])
    async def play(self, ctx: vbu.Context, kahoot: str = None):
        """
        Plays a quiz
        """
         # Make sure they're not already playing
        if ctx.channel.id in KahootGame.kahoot_sessions:
            return await ctx.send("A game is already being hosted in this channel!")

        # Add the channel to the set of kahoot sessions
        password = utils.get_password()
        KahootGame.add_session(ctx.channel.id, password)

        # Send the user the password
        await ctx.author.send(f"You have started a Kahoot game! If you must cancel the game at any point, run `/cancel {password}` in the channel of the game. Enjoy!")

        # Get the requester
        _, requester = await utils.setup_kahoot(ctx, kahoot)
        if not requester:
            return KahootGame.remove_session(ctx.channel.id)
        # Get the players
        players_dict = await utils.get_players(ctx, requester)
        if not players_dict:
            return KahootGame.remove_session(ctx.channel.id)

        questions = requester.get_questions()

        # Set the shuffle
        shuffle = list(questions.keys())
        random.shuffle(shuffle)

        kahoot_game = KahootGame(requester, players_dict, shuffle, ctx)
        kahoot_game.play_game()


        sorted_player_list = sorted(players_dict.items(), key=lambda x: x[1], reverse=True)

        try:
            await ctx.send(f"**__Winner__**\n{sorted_player_list[0][0].mention}\n\n**__Total Points__**\n" + "\n".join([f"{player.mention} - {score} ({int(score/len(shuffle) * 100)}%)" for player, score in sorted_player_list]))
        except ZeroDivisionError:
            pass

        # Remove the lock
        if ctx.channel.id in KahootGame.get_sessions():
            return KahootGame.remove_session(ctx.channel.id)



def setup(bot: vbu.Bot):
    x = KahootCommand(bot)
    bot.add_cog(x)
