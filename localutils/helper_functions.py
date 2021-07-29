import re

MATCHER = re.compile(r'[0-9a-zA-Z-]{35,}')

def find_id(input_string):
    """
    This function takes a string and returns the id of the quiz
    :param input_string: string
    :return: string
    """

    return MATCHER.search(input_string)[0]
