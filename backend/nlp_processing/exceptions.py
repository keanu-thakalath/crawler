class NLPProcessingError(Exception):
    pass


class UnsupportedModelError(NLPProcessingError):
    def __init__(self, model: str, reason: str):
        self.model = model
        self.reason = reason
        super().__init__(f"Model '{model}' is not supported: {reason}")
