import random
import string

from faker import Faker


class Identity(object):
    def __init__(self):
        self.fake = Faker()

    @staticmethod
    def _generate_password() -> str:
        password_characters = string.ascii_letters + string.digits
        return "".join(random.choice(password_characters) for _ in range(12))

    @staticmethod
    def _generate_new_username(username: str) -> str:
        first_name, last_name = username.split(" ")
        new_username = str(
            first_name.lower()[:3] + last_name.lower()[:4] + str(random.randint(1, 999))
        )
        return new_username

    def get_identity(self) -> dict:
        """ Create Fake User Identity"""
        gender = random.choice(["female", "male"])

        if gender == "male":
            first_name = self.fake.first_name_female()
            last_name = self.fake.last_name_female()
            full_name = first_name + " " + last_name
        else:
            first_name = self.fake.first_name_female()
            last_name = self.fake.last_name_female()
            full_name = first_name + " " + last_name

        username = str(
            first_name.lower()[:3] + last_name.lower()[:4] + str(random.randint(1, 999))
        )

        identity = {
            "name": full_name,
            "username": username,
            "gender": gender,
            "birthday": self.fake.date_of_birth(
                tzinfo=None, minimum_age=18, maximum_age=40
            ),
            "password": self._generate_password(),
            "email": f"{username}@trafficrobot.tk",  # todo: create generator mail
            "proxy": "",
        }

        return identity
