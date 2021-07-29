import aiohttp

class KahootRequester(object):
    def __init__(self, quiz_data):
        self.quiz_data = quiz_data

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
        return self.quiz_data["card"]["title"]
    
    def get_description(self):
        return self.quiz_data["card"]["description"]

    def get_thumbnail(self):
        return self.quiz_data["card"]["cover"]

    def get_questions(self):
        return self.quiz_data["kahoot"]["questions"]

    def get_question_count(self):
        return len(self.get_questions())