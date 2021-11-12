import voxelbotutils as vbu
from datetime import datetime as dt
import re
import asyncio
import random
import string

import discord

from localutils.requester import KahootRequester

MATCHER = re.compile(r'[0-9a-zA-Z-]{35,}')

BASE_DATA_URL = "https://create.kahoot.it/rest/kahoots/{}/card/?includeKahoot=true"
BASE_KAHOOT_URL = "https://create.kahoot.it/details/{}"

MAX_PLAYERS = 20

def find_id(input_string):
    """
    This function takes a string and returns the id of the quiz
    :param input_string: string
    :return: string
    """

    return MATCHER.search(input_string)[0]

def get_data_link(kahoot_id):
    """
    This function takes a kahoot_id and returns the quiz
    :param kahoot_id: string
    :return: string
    """

    return BASE_DATA_URL.format(kahoot_id)

def get_quiz_link(kahoot_id):
    """
    This function takes a kahoot_id and returns the quiz link
    :param kahoot_id: string
    :return: string
    """

    return BASE_KAHOOT_URL.format(kahoot_id)

async def setup_kahoot(ctx, kahoot):
    # Get a message
    if not kahoot:
        await ctx.send("What quiz would you like to play? (Either the link or the long ID from <https://create.kahoot.it/>)")
        try:
            kahoot = await ctx.bot.wait_for("message", timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        except asyncio.TimeoutError:
            await ctx.send("Still there? Timing Out due to inactivity.")
        kahoot = kahoot.content

    # Make sure we got an ID
    try:
        kahoot_id = find_id(kahoot)
    except TypeError:
        await ctx.send("I couldn't find a valid ID in your message.")
        return (None, None)

    # Get the quiz link
    quiz_link = get_data_link(kahoot_id)

    # Get a requester object
    requester = await KahootRequester.get_quiz_data(quiz_link)

    # Make sure the game is valid
    if not requester.is_valid:
        await ctx.send("No game was found with the given ID.")
        return (None, None)

    return (kahoot_id, requester)

def get_date(unix_time):
    """
    This function takes a unix time and returns the date
    :param unix_time: int
    :return: datetime
    """

    return dt.utcfromtimestamp(unix_time / 1000).strftime('%Y-%m-%d') # Divide by 1000 to get seconds from milliseconds

def get_footer_text(creator_name:str = None, created_at:dt = None):
    """
    This function takes a creator_name and returns the footer text
    :param creator_name: string
    :param created_at: dt
    :return: string
    """
    footer_text = ""

    if creator_name:
        footer_text += f"Created by {creator_name}"
    if created_at:
        footer_text += f" • {created_at}"

    return footer_text

def get_footer_items(creator_name:str = None, created_at:dt = None, creator_icon:str = None):
    """
    This function takes a creator_name and returns the footer text
    :param creator_name: string
    :param created_at: dt
    :param
    :return: dict
    """
    footer_text = get_footer_text(creator_name, created_at)

    footer_items = {}

    if footer_text:
        footer_items["text"] = footer_text
    if creator_icon:
        footer_items["icon_url"] = creator_icon

    return footer_items

async def update_component_message(message, components, message_content=None):
    """
    This function takes the join-game message and updates it with the given content
    """
    # If we have a join message with an embed
    if message.embeds:
        # Get the embed
        embed = message.embeds[0]

        # Update the embed
        if embed.fields:
            curr_field = embed.fields[0]
            embed.set_field_at(0, name=curr_field.name, value=message_content)
        else:
            embed.description = message_content or embed.description

        await message.edit(embed=embed, components=components)
    else:
        await message.edit(content=message_content, components=components) if message_content else await message.edit(components=components)

async def disable_components(message, components, message_content=None):
    """
    This function disables the components of a message
    """
    # Disable the components
    components.disable_components()

    # Update the message
    await update_component_message(message, components, message_content)

async def get_players(ctx, requester):
    """
    This function gets the players for a game
    """
    # Get the players
    players = {}
    # Set up the buttons
    join_button = discord.ui.Button(label = f"Join 0/{MAX_PLAYERS}", custom_id = "join",  style=discord.ui.ButtonStyle.success)
    continue_button = discord.ui.Button(label = f"Continue", custom_id = "continue",  style=discord.ui.ButtonStyle.secondary)
    cancel_button = discord.ui.Button(label = f"Cancel", custom_id = "cancel",  style=discord.ui.ButtonStyle.danger)

    # Put the buttons together
    components = discord.ui.MessageComponents(
        discord.ui.ActionRow(join_button, continue_button, cancel_button)
    )

    # Send the message with the buttons, wait for a response, then acknowledge the interaction
    embed = vbu.Embed()
    embed.title = requester.get_title()
    thumbnail = requester.get_thumbnail()
    embed.set_thumbnail(url=thumbnail) if thumbnail else None
    embed.description = "Press \"Join\" to join the game!"

    embed.add_field(name="Players", value="No one has joined yet!")

    join_message = await ctx.send(embed=embed, components=components)

    def check(p):

        if p.message.id != join_message.id:
            return False

        if p.component.custom_id.lower() == "cancel":
            ctx.bot.loop.create_task(p.response.defer_update())

            if p.user == ctx.author:
                return True

            return False

        if p.component.custom_id.lower() == "continue":
            ctx.bot.loop.create_task(p.response.defer_update())

            if p.user == ctx.author:
                return True

            return False

        if p.user in players.keys():
            ctx.bot.loop.create_task(p.response.defer_update())

            return False

        players[p.user] = 0

        ctx.bot.loop.create_task(p.response.send_message("You have joined the game!", ephemeral=True))

        player_count = len(players.keys())
        join_button.label = f"Join {player_count}/{MAX_PLAYERS}"

        if join_message.embeds:
            update_string = '\n'.join([player.mention for player in players.keys()])
        else:
            update_string = "Press \"Join\" to join the game!\n**Players**:\n" + '\n'.join([player.mention for player, _ in players])

        ctx.bot.loop.create_task(update_component_message(join_message, components, update_string))

        return player_count >= MAX_PLAYERS

    try:
        payload = await ctx.bot.wait_for("component_interaction", check=check, timeout=120)
        if payload.component.custom_id.lower() == "cancel":
            await ctx.send("The game has been cancelled.")
            await disable_components(join_message, components)
            return
    except asyncio.TimeoutError:
        pass

    await disable_components(join_message, components,'\n'.join([player.mention for player in players.keys()]))

    return players

def get_random_message(correct):
    """
    This function returns a random formatted "Good Job" or "Wrong" message based on if it is correct
    """
    output = "**"

    if correct:
        output += random.choice(["Congrats!", "Nice!", "Correct!", "Good job!"])
    else:
        output += random.choice(["No one got it!", "Wrong!", "That's not right!", "Not quite!", "Not quite right!"])

    output += "**\n"

    return output

def get_password():

    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))