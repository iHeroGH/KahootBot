import voxelbotutils as vbu
from datetime import datetime as dt
import re
import asyncio

from localutils.requester import KahootRequester

MATCHER = re.compile(r'[0-9a-zA-Z-]{35,}')

BASE_DATA_URL = "https://create.kahoot.it/rest/kahoots/{}/card/?includeKahoot=true"
BASE_KAHOOT_URL = "https://create.kahoot.it/details/{}"

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
        await ctx.send("What quiz would you like to play? (Either the link or the long ID)")
        kahoot = await ctx.bot.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
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

async def get_players(ctx):
    """
    This function gets the players for a game
    """
    # Get the players
    players = {}
    # Set up the buttons
    join_button = vbu.Button(f"Join 0/5", "join",  style=vbu.ButtonStyle.SUCCESS)
    continue_button = vbu.Button(f"Continue", "continue",  style=vbu.ButtonStyle.SECONDARY)

    # Put the buttons together 
    components = vbu.MessageComponents(
        vbu.ActionRow(join_button, continue_button)
    )

    # Send the message with the buttons, wait for a response, then acknowledge the interaction
    join_message_content = ["Press \"Join\" to join the game!\n**Players:**\n"]
    join_message = await ctx.send(join_message_content[0], components=components)

    def check(p):

        if p.message.id != join_message.id:
            return False
        
        ctx.bot.loop.create_task(p.ack())

        if p.component.custom_id.lower() == "continue" and len(players) > 1:
            if p.user == ctx.author:
                return True
            else:
                return False

        if p.user in players.keys():
            return False

        players[p.user] = 0
        join_message_content.append(join_message_content.pop() + f"{p.user.mention}\n")

        player_count = len(players.keys())
        join_button.label = f"Join {player_count}/5"

        ctx.bot.loop.create_task(update_component_message(join_message, components,  join_message_content[0]))
        
        return player_count >= 5

    try:
        payload = await ctx.bot.wait_for("component_interaction", check=check, timeout=60)
    except asyncio.TimeoutError:
        await disable_components(join_message, components, join_message_content[0])
    
    await disable_components(join_message, components, join_message_content[0])

    if len(players) > 1:
        return players
    else:
        await ctx.send("The game has been cancelled since there are too few players.")
        return


