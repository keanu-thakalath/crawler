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


class JobNotFoundError(ServiceError):
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")


class InvalidJobTypeError(ServiceError):
    def __init__(self, job_id: str, job_type: str):
        self.job_id = job_id
        self.job_type = job_type
        super().__init__(f"Job {job_id} does not support review status updates (outcome type: {job_type})")


class InvalidSummaryValueError(ServiceError):
    def __init__(self, summary: str):
        self.summary = summary
        super().__init__(f"Summary cannot be empty or whitespace-only")
