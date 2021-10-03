from localutils.helper_functions import disable_components
import voxelbotutils as vbu
import localutils as utils

import discord

import asyncio
import random

class KahootCommand(vbu.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.kahoot_sessions = set()

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
        # Make sure they're not already playing
        if ctx.channel.id in self.kahoot_sessions:
            return await ctx.send("A game is already being hosted in this channel!")

        # Add the channel to the set of kahoot sessions
        self.kahoot_sessions.add(ctx.channel.id)

        # Get the requester
        _, requester = await utils.setup_kahoot(ctx, kahoot)
        if not requester:
            return self.kahoot_sessions.remove(ctx.channel.id)

        # Get the players
        players_dict = await utils.get_players(ctx, requester)
        if not players_dict:
            return self.kahoot_sessions.remove(ctx.channel.id)
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
            question_type, answers, question_img = questions[shuffle_obj]

            # Set up the answer buttons
            action_rows = []
            correct_answers = []
            correct_answer_strings = []
            for i, answer in enumerate(answers):
                answer_string = answer[0]
                answer_button = discord.ui.Button(answer_string, "answer" + str(i),  style=discord.ui.ButtonStyle.secondary)
                action_row = discord.ui.ActionRow(answer_button)
                action_rows.append(action_row)

                if answer[1]:
                    correct_answers.append(answer_button)
                    correct_answer_strings.append(answer_string)

            # Put the buttons together
            components = discord.ui.MessageComponents(
                *action_rows
            )

            # Set up the embed
            embed = vbu.Embed()
            embed.color = 5047956
            embed.description = question + ("\n(The next thing you type will be registered as your answer)" if question_type == 'open_ended' else "")
            if question_img:
                embed.set_image(url=question_img)
            total_question_count = requester.get_question_count()
            embed.set_footer(requester.get_title() + " • " + f"{total_question_count - len(shuffle)}/{total_question_count}")

            params = {
                'embed': embed
            }
            if question_type != 'open_ended':
                params['components'] = components

            question_message = await ctx.send(**params)

            answered = []
            correct = []
            def check(p):

                if p.message.id != question_message.id:
                    return False

                if p.user not in players_dict.keys() or p.user in answered:
                    ctx.bot.loop.create_task(p.ack())
                    return False
                else:
                    answered.append(p.user)
                    ctx.bot.loop.create_task(p.respond(f"You chose \"**{p.component.label}**\"!", ephemeral=True))

                if p.component in correct_answers:
                    correct.append(p.user)
                    players_dict[p.user] += 1

                return len(answered) == player_count

            def open_ended_check(message):
                if message.channel.id != question_message.channel.id:
                    return False
                if message.author not in players_dict.keys() or message.author in answered:
                    return False
                else:
                    answered.append(message.author)
                    ctx.bot.loop.create_task(message.ack())

                if message.content.lower() in correct_answer_strings:
                    correct.append(message.author)
                    players_dict[message.author] += 1

                return len(answered) == player_count

            try:
                if question_type == 'open_ended':
                    await ctx.bot.wait_for('message', check=open_ended_check, timeout=60)
                else:
                    await ctx.bot.wait_for("component_interaction", check=check, timeout=30)
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
            if len(correct_answers) > 1:
                correct_answers_string = '**\" and \"**'.join([answer.label for answer in correct_answers])
                correct_answers_string = f"The correct answers were \"**{correct_answers_string}**\""
            else:
                correct_answers_string = f"The correct answer was \"**{correct_answers[0].label}**\""

            output_message = correct_answers_string + "\n\n"
            output_message += utils.get_random_message(correct)
            output_message += "\n".join([i.mention for i in correct]) if correct else ""
            await ctx.send(output_message)

            await asyncio.sleep(5)


        sorted_player_list = sorted(players_dict.items(), key=lambda x: x[1], reverse=True)

        await ctx.send(f"**__Winner__**\n{sorted_player_list[0][0].mention}\n\n**__Total Points__**\n" + "\n".join([f"{player.mention} - {score} ({int(score/total_question_count * 100)}%)" for player, score in sorted_player_list]))

        # Remove the lock
        self.kahoot_sessions.remove(ctx.channel.id)



def setup(bot: vbu.Bot):
    x = KahootCommand(bot)
    bot.add_cog(x)
