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
