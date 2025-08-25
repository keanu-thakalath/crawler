from sqlalchemy import MetaData
from sqlalchemy.orm import registry

metadata = MetaData()
mapper_registry = registry()

__all__ = ["metadata", "mapper_registry"]
