from collections.abc import AsyncGenerator

from litestar.datastructures import State
from litestar.di import Provide

from service.unit_of_work import SqlAlchemyUnitOfWork, UnitOfWork


async def _provide_uow(state: State) -> AsyncGenerator[UnitOfWork, None]:
    session_factory = state.session_factory
    async with SqlAlchemyUnitOfWork(session_factory=session_factory) as uow:
        yield uow


provide_uow = Provide(_provide_uow)
