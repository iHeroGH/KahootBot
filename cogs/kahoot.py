from localutils.helper_functions import disable_components
from discord.ext.commands.errors import CommandInvokeError
import voxelbotutils as vbu
import localutils as utils

import asyncio
import random

class KahootCommand(vbu.Cog):

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

    @vbu.command(aliases=['kahoot', 'quiz'])
    async def play(self, ctx: vbu.Context, kahoot: str = None):
        """
        Plays a quiz
        """
        # Get the requester
        _, requester = await utils.setup_kahoot(ctx, kahoot)
        if not requester:
            return

        # Get the players
        players_dict = await utils.get_players(ctx)
        if not players_dict:
            return
        player_count = len(players_dict.keys())

        questions = requester.get_questions()

        # Set the shuffle
        shuffle = list(questions.keys())
        random.shuffle(shuffle)

        strikes = 0
        while shuffle:
            # Get a question and go to the next in the shuffle
            shuffle_obj = shuffle.pop(0)
            question, _ = shuffle_obj

            # Set up the question variables
            answers, question_img = questions[shuffle_obj]

            # Set up the answer buttons
            action_rows = []
            correct_answers = []
            for i, answer in enumerate(answers):
                answer_button = vbu.Button(answer[0], "answer" + str(i),  style=vbu.ButtonStyle.SECONDARY)
                action_row = vbu.ActionRow(answer_button)
                action_rows.append(action_row)

                correct_answers.append(answer_button) if answer[1] else None
            
            # Put the buttons together 
            components = vbu.MessageComponents(
                *action_rows
            )

            # Set up the embed
            embed = vbu.Embed()
            embed.color = 5047956
            embed.description = question
            embed.set_image(url=question_img)
            total_question_count = requester.get_question_count()
            #print(shuffle, len(shuffle))
            embed.set_footer(requester.get_title() + " • " + f"{total_question_count - len(shuffle)}/{total_question_count}")
            question_message = await ctx.send(embed=embed, components=components)
            
            answered = []
            correct = []
            def check(p):

                if p.message.id != question_message.id:
                    return False
                
                ctx.bot.loop.create_task(p.ack())

                if p.user not in players_dict.keys() or p.user in answered:
                    return False
                else:
                    answered.append(p.user)
                
                if p.component in correct_answers:
                    correct.append(p.user)
                    players_dict[p.user] += 1
                
                return len(answered) == player_count

            try:
                payload = await ctx.bot.wait_for("component_interaction", check=check, timeout=30)
            except asyncio.TimeoutError:
                if not answered:
                    strikes += 1
                if strikes == 3:
                    break
                await disable_components(question_message, components)

            if answered:
                strikes = 0


            await disable_components(question_message, components)

            # Send a final message
            await ctx.send("**" + random.choice(["Congrats!", "Nice!", "Correct!", "Good job!"]) + "**\n" + "\n".join([i.mention for i in correct])) if correct else await ctx.send("**" + random.choice(["No one got it!", "Wrong!", "That's not right!", "Not quite!", "Not quite right!"]) + "**")

            await asyncio.sleep(5)


        await ctx.send("**__Total Points__**\n" + "\n".join([f"{i.mention} - {players_dict[i]} ({(players_dict[i]/total_question_count) * 100}%)" for i in players_dict.keys()]))



        
def setup(bot: vbu.Bot):
    x = KahootCommand(bot)
    bot.add_cog(x)
