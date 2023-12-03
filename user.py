import json, os, Components
from response import Response
from command import RouteCommand, KeywordCommand
from Components import Keyword, Route, load_keyword_w_id, load_route_w_id, Address

user_dir = "data/user"
user_file_extension = "usr"


class User:
    def __init__(self, phone_number: str, password: str, routes: list[str],
                 keywords: list[str], credit: float):
        self.phone_number = phone_number
        self.password = password
        self.routes = routes
        self.keywords = keywords
        self.credit = credit

    def get_number(self):
        return self.phone_number

    def get_password(self):
        return self.password

    def set_password(self, password: str):
        self.password = password

    def get_routes(self):
        return self.routes

    def add_route(self, route):
        if type(route) is Route:
            r_id = str(route.route_id).zfill(12)
        else:
            r_id = str(route).zfill(12)
        print(r_id)
        self.routes.append(r_id)

    def contains_route_name(self, route_name: str):
        route_name = route_name.lower()
        for route in self.routes:
            r = load_route_w_id(route)
            if type(r) is Route:
                if r.key.lower() == route_name:
                    return True
        return False

    def get_route_w_name(self, route_name: str):
        route_name = route_name.lower()
        for route in self.routes:
            r = load_route_w_id(route)
            if type(r) is Route:
                if r.key.lower() == route_name:
                    return r
        return False

    def remove_route(self, route_name: str):
        route_name = route_name.lower()
        for index, route_id in enumerate(self.routes):
            r = load_route_w_id(route_id)
            if type(r) is Route:
                if r.key == route_name:
                    self.routes.pop(index)
                    return True
        return False

    def get_keywords(self):
        return self.keywords

    def get_keywords_formatted(self):
        formatted = ""
        remove_keys = []
        for key_id in self.keywords:
            keyword = Components.load_keyword_w_id(key_id)
            if not keyword:
                # found a keyword that does not exist
                remove_keys.append(key_id)
            else:
                formatted += f"{keyword.key}: {keyword.value}\n"
        formatted.strip()
        return formatted

    def contains_keyword_name(self, keyword_name: str):
        keyword_name = keyword_name.lower()
        for key_id in self.keywords:
            keyword = load_keyword_w_id(key_id)
            if keyword.key.lower() == keyword_name:
                return True
        return False

    def add_keyword(self, keyword):
        """Receives either keyword object or a string that contains a keyword's ID"""
        if type(keyword) is Keyword:
            key_id = keyword.id
            keyword.save()
        else:
            key_id = f"{keyword}".zfill(12)
        self.keywords.append(key_id)

    def remove_keyword(self, keyword_name: str):
        keyword_name = keyword_name.lower()
        for index, keyword in enumerate(self.keywords):
            current_keyword = Components.load_keyword_w_id(keyword)
            if current_keyword:
                if current_keyword.key == keyword_name:
                    return self.keywords.pop(index)
        return False

    def remove_keyword_w_id(self, keyword_id: str):
        keyword_id = keyword_id.zfill(12)
        for index, key_id in enumerate(self.keywords):
            if key_id == keyword_id:
                self.keywords.pop(index)
                return True
        return False

    def get_credits(self):
        return self.credit

    def set_credits(self, credit):
        self.credit = credit

    def save(self):
        user_dict = {
            "phone_number": self.phone_number,
            "password": self.password,
            "routes": self.routes,
            "keywords": self.keywords,
            "credit": self.credit
        }
        with open(f"{user_dir}/{self.phone_number}.{user_file_extension}", "w") as user_file:
            json.dump(user_dict, user_file, indent=4)


def load_user(user_number):
    user_file_names = os.listdir(user_dir)
    user_data = {}
    for user_file_name in user_file_names:
        if user_file_name == f"{user_number}.{user_file_extension}":
            with open(f"{user_dir}/{user_file_name}") as user_file:
                user_data = json.load(user_file)
            break
    if user_data:
        user = User(user_data.get("phone_number"), user_data.get("password"), user_data.get("routes"),
                    user_data.get("keywords"), user_data.get("credit"))
        return user
    return False


