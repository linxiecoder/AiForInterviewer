"""Repository base placeholder."""

from sqlalchemy.orm import Session


class SqlAlchemyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

