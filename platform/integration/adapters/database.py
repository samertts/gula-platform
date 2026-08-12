from dataclasses import dataclass, field
from typing import Any


@dataclass
class DatabaseConfig:
    url: str = ""
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 1800
    pool_pre_ping: bool = True
    echo: bool = False
    connect_timeout: int = 5
    statement_timeout: str = "30s"
    read_replica_url: str | None = None
    read_replica_pool_size: int = 5
    read_replica_max_overflow: int = 10


class DatabaseAdapter:
    def __init__(self, config: DatabaseConfig | None = None):
        self._config = config or DatabaseConfig()
        self._engine = None
        self._read_engine = None
        self._session_factory = None
        self._read_session_factory = None

    async def connect(self) -> None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        connect_args = {"connect_timeout": self._config.connect_timeout}
        self._engine = create_engine(
            self._config.url,
            pool_size=self._config.pool_size,
            max_overflow=self._config.max_overflow,
            pool_recycle=self._config.pool_recycle,
            pool_pre_ping=self._config.pool_pre_ping,
            echo=self._config.echo,
            connect_args=connect_args,
        )
        self._session_factory = sessionmaker(bind=self._engine)

        if self._config.read_replica_url:
            self._read_engine = create_engine(
                self._config.read_replica_url,
                pool_size=self._config.read_replica_pool_size,
                max_overflow=self._config.read_replica_max_overflow,
                pool_recycle=self._config.pool_recycle,
                pool_pre_ping=self._config.pool_pre_ping,
                echo=self._config.echo,
            )
            self._read_session_factory = sessionmaker(bind=self._read_engine)

    async def disconnect(self) -> None:
        if self._engine:
            self._engine.dispose()
        if self._read_engine:
            self._read_engine.dispose()

    def session(self) -> Any:
        if self._session_factory is None:
            raise RuntimeError("Database not connected")
        return self._session_factory()

    def read_session(self) -> Any:
        if self._read_session_factory:
            return self._read_session_factory()
        return self.session()

    @property
    def engine(self) -> Any:
        return self._engine

    async def health(self) -> dict[str, Any]:
        status = {"primary": "unknown", "replica": "unknown"}
        try:
            with self._engine.connect() as conn:
                conn.execute(conn.text("SELECT 1"))
            status["primary"] = "ok"
        except Exception as e:
            status["primary"] = str(e)
        if self._read_engine:
            try:
                with self._read_engine.connect() as conn:
                    conn.execute(conn.text("SELECT 1"))
                status["replica"] = "ok"
            except Exception as e:
                status["replica"] = str(e)
        return status

    def is_connected(self) -> bool:
        return self._engine is not None
