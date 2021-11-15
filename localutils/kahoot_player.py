import discord
from discord.ext.commands.context import Context
import voxelbotutils as vbu

from localutils.requester import KahootRequester
from localutils.helper_functions import disable_components
import localutils as utils

import asyncio

class KahootGame:

    kahoot_sessions = dict()

    def __init__(self, requester: KahootRequester, players_dict: dict, shuffle: list, ctx: Context):
        self.requester = requester
        self.questions = requester.get_questions()

        self.players_dict = players_dict
        self.player_count = len(self.players_dict.keys())

        self.shuffle = shuffle
        self.total_question_count = len(shuffle)

        self.ctx = ctx

    @staticmethod
    def add_session(channel_id, password):
        KahootGame.kahoot_sessions[channel_id] = password

    @property
    def kahoot_sessions():
        return KahootGame.kahoot_sessions

    @staticmethod
    def remove_session(channel_id):
        KahootGame.kahoot_sessions.pop(channel_id)

    async def play_game(self):
        strikes = 0
        while self.shuffle:
            # If the game was cancelled prematurely
            if self.ctx.channel.id not in KahootGame.kahoot_sessions.keys():
                self.shuffle = []
                break
            # Get a question and go to the next in the shuffle
            shuffle_obj = self.shuffle.pop(0)
            question, _ = shuffle_obj

            # Set up the question variables
            question_type, answers, question_img, question_video = self.questions[shuffle_obj]

            # Set up the answer buttons
            action_rows = []
            correct_answers = []
            correct_answer_strings = []
            for i, answer in enumerate(answers):
                answer_string = answer[0]
                answer_button = discord.ui.Button(label=answer_string, custom_id="answer" + str(i),  style=discord.ui.ButtonStyle.secondary)
                action_row = discord.ui.ActionRow(answer_button)
                action_rows.append(action_row)

                if answer[1]:
                    correct_answers.append(answer_button)
                    correct_answer_strings.append(answer_string.lower())

            # Put the buttons together
            components = discord.ui.MessageComponents(
                *action_rows
            )

            # Set up the embed
            embed = vbu.Embed()
            embed.color = 5047956
            embed.description = question
            embed.description += "\n(The next thing you type will be registered as your answer)" if question_type == 'open_ended' else ""
            embed.description += f"\nVideo Link: {question_video}" if question_video else ""
            if question_img:
                embed.set_image(url=question_img)
            embed.set_footer(self.requester.get_title() + " • " + f"{self.total_question_count - len(self.shuffle)}/{self.total_question_count}")

            params = {
                'embed': embed
            }
            if question_type != 'open_ended':
                params['components'] = components

            question_message = await self.ctx.send(**params)

            answered = []
            correct = []
            def check(p):

                if p.message.id != question_message.id:
                    return False

                if p.user not in self.players_dict.keys() or p.user in answered:
                    self.ctx.bot.loop.create_task(p.response.defer_update())
                    return False
                else:
                    answered.append(p.user)
                    self.ctx.bot.loop.create_task(p.response.send_message(f"You chose \"**{p.component.label}**\"!", ephemeral=True))

                if p.component in correct_answers:
                    correct.append(p.user)
                    self.players_dict[p.user] += 1

                return len(answered) == self.player_count

            def open_ended_check(message):
                if message.channel.id != question_message.channel.id:
                    return False
                if message.author not in self.players_dict.keys() or message.author in answered:
                    return False
                else:
                    answered.append(message.author)
                    self.bot.loop.create_task(message.add_reaction("✅"))

                if message.content.lower() in correct_answer_strings:
                    correct.append(message.author)
                    self.players_dict[message.author] += 1

                return len(answered) == self.player_count

            try:
                if question_type == 'open_ended':
                    await self.ctx.bot.wait_for('message', check=open_ended_check, timeout=120)
                else:
                    await self.ctx.bot.wait_for("component_interaction", check=check, timeout=60)
            except asyncio.TimeoutError:
                if not answered:
                    strikes += 1
                if strikes == 3:
                    break
                if question_type != 'open-ended':
                    await disable_components(question_message, components)

            if answered:
                strikes = 0

            await disable_components(question_message, components)

            # Send a final message
            if len(correct_answers) > 1:
                correct_answers_string = '**\" and \"**'.join([answer.label for answer in correct_answers])
                correct_answers_string = f"The correct answers were \"**{correct_answers_string}**\""
            elif not correct_answers:
                correct_answers_string = f"There were no correct answers!"
            else:
                correct_answers_string = f"The correct answer was \"**{correct_answers[0].label}**\""

            output_message = correct_answers_string + "\n\n"
            output_message += utils.get_random_message(correct)
            output_message += "\n".join([i.mention for i in correct]) if correct else ""
            await self.ctx.send(output_message)

            await asyncio.sleep(5)