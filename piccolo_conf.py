import os
from urllib.parse import unquote, urlparse

from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

APP_REGISTRY = AppRegistry(apps=["app.piccolo_app"])


def engine_from_env() -> PostgresEngine:
    """DATABASE_URL is the direct Postgres string. Migrations only."""
    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        return PostgresEngine(config={})
    parsed = urlparse(raw)
    return PostgresEngine(
        config={
            "host": parsed.hostname or "",
            "port": parsed.port or 5432,
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "database": parsed.path.lstrip("/") or "postgres",
        }
    )


DB = engine_from_env()
