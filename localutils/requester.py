import aiohttp

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
        return self.card_data["title"]
    
    def get_description(self):
        return self.card_data["description"]

    def get_thumbnail(self):
        return self.card_data["cover"]

    def get_popularity(self):
        plays, players, favorites = self.card_data["number_of_plays"], self.card_data["number_of_players"], self.card_data["total_favourites"]        
        return f"{plays} Plays\n{players} Players\n{favorites} Favorites"

    def get_creator(self):
        return self.card_data["creator_username"], self.card_data["creator_avatar"]["url"]

    def get_created_at(self):
        return self.card_data["created"]

    def get_question_count(self):
        return self.card_data["number_of_questions"]

    def get_questions(self):
        return self.quiz_data["kahoot"]["questions"]
    
