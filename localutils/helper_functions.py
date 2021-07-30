from datetime import datetime as dt
import re

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

def get_date(unix_time):
    """
    This function takes a unix time and returns the date
    :param unix_time: int
    :return: datetime
    """

    return dt.utcfromtimestamp(unix_time / 1000).strftime('%Y-%m-%d') # Divide by 1000 to get seconds from milliseconds

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

def get_footer_text(creator_name:str = None, created_at:dt = None):
    """
    This function takes a creator_name and returns the footer text
    :param creator_name: string
    :param created_at: dt
    :return: string
    """
    footer_text = ""

    if creator_name:
        footer_text += f"{creator_name}"
    if created_at:
        footer_text += f" • Created {created_at}"

    return footer_text