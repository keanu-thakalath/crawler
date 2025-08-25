class DomainError(Exception):
    pass


class InvalidUrlError(Exception):
    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Invalid URL '{url}': {reason}")
