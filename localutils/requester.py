import aiohttp
import humanize


class KahootRequester(object):
    def __init__(self, quiz_data):
        self.quiz_data = quiz_data
        self.card_data = self.quiz_data["card"]

    @classmethod
    async def get_quiz_data(cls, quiz_link):
        async with aiohttp.ClientSession() as session:
            async with session.get(quiz_link) as resp:
                return cls(await resp.json())

    def is_valid(self):
        if "error" in self.quiz_data.keys():
            return False
        return True

    def get_title(self):
        title = None
        if "title" in self.card_data.keys():
            title = self.card_data["title"]

        return title

    def get_description(self):
        description = None
        if "description" in self.card_data.keys():
            description = self.card_data["description"]

        return description

    def get_thumbnail(self):
        thumbnail = None
        if "cover" in self.card_data.keys():
            thumbnail = self.card_data["cover"]

        return thumbnail

    def get_popularity(self):
        # Set up the popularity variables
        if "number_of_plays" in self.card_data.keys():
            plays = self.card_data["number_of_plays"]
            plays = humanize.intcomma(plays)
        if "number_of_players" in self.card_data.keys():
            players = self.card_data["number_of_players"]
            players = humanize.intcomma(players)
        if "total_favourites" in self.card_data.keys():
            favorites = self.card_data["total_favourites"]
            favorites = humanize.intcomma(favorites)

        # Set up the popularity string
        popularity_string = ""
        if plays:
            popularity_string += f"{plays} Plays\n"
        if players:
            popularity_string += f"{players} Players\n"
        if favorites:
            popularity_string += f"{favorites} Favorites"

        # Return it
        return popularity_string

    def get_creator(self):
        # Set up the creator variables
        username, avatar = None, None

        # Make sure username exists
        if "creator_username" in self.card_data.keys():
            username = self.card_data["creator_username"]
        # Make sure avatar exists
        if "creator_avatar" in self.card_data.keys():
            if "url" in self.card_data["creator_avatar"].keys():
                avatar = self.card_data["creator_avatar"]["url"]

        return username, avatar

    def get_created_at(self):
        created_at = None
        if "created" in self.card_data.keys():
            created_at = self.card_data["created"]

        return created_at

    def get_question_count(self):
        question_count = None
        if "number_of_questions" in self.card_data.keys():
            question_count =  self.card_data["number_of_questions"]

        return question_count

    def get_questions(self):
        questions = {}

        if not self.quiz_data['kahoot']['questions']:
            return

        # Loop through the questions
        custom_id = 0
        for question_obj in self.quiz_data['kahoot']['questions']:
            question_type = question_obj['type'] # Type of question
            question_text = question_obj['question'] # Text of question

            # Question image if it exists
            question_img = None
            if 'image' in question_obj.keys():
                question_img = question_obj['image']

            # Answers
            answers = []
            for answer_obj in question_obj['choices']:
                answer_obj = (self.fix_text(answer_obj['answer']), answer_obj['correct'])
                # Add the answer object tuple to the list
                answers.append(answer_obj)

            questions[(self.fix_text(question_text), custom_id)] = (question_type, answers, question_img)
            custom_id += 1

        return questions


    def fix_text(self, text):
        """
        This function takes a string and returns a string with all the special & characters replaced with their normal characters
        :param text: string
        :return: string
        """

        return text.replace('&amp;', '&').replace('&nbsp;', ' ').replace('&quot;', '"').replace('&apos;', "'").replace("<b>", "**").replace("</b>", "**").replace("<i>", "*").replace("</i", "*")