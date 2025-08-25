class ServiceError(Exception):
    pass


class SourceAlreadyExistsError(ServiceError):
    def __init__(self, url: str):
        self.url = url
        super().__init__(f"Source already exists: {url}")


class PageAlreadyExistsError(ServiceError):
    def __init__(self, url: str):
        self.url = url
        super().__init__(f"Page already exists: {url}")


class PageNotFoundError(ServiceError):
    def __init__(self, url: str):
        self.url = url
        super().__init__(f"Page not found: {url}")


class SourceNotFoundError(ServiceError):
    def __init__(self, url: str):
        self.url = url
        super().__init__(f"Source not found: {url}")
