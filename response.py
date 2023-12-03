
class Response:
    def __init__(self, value, message=""):
        self.value = value
        if not message:
            message = None
        self.message = message

    def __str__(self):
        return f"{self.value} | {self.message}"


