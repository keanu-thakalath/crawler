from . import mapper_registry, metadata
from .entities import map_entities
from .values import map_values


class Models:
    _mappers_started = False

    @classmethod
    def start_mappers(cls):
        if cls._mappers_started:
            return
        cls._mappers_started = True
        (
            job_error_mapper,
            scrape_result_mapper,
            extract_result_mapper,
            summarize_result_mapper,
            crawl_result_mapper,
        ) = map_values()

        map_entities(
            job_error_mapper,
            scrape_result_mapper,
            extract_result_mapper,
            summarize_result_mapper,
            crawl_result_mapper,
        )


__all__ = ["metadata", "mapper_registry", "Models"]
