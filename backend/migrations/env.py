import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool, create_engine
from alembic import context

# ------------------------------------------------------------------------------
# 1. Path Setup: Ensure project root & backend directory are on sys.path
# ------------------------------------------------------------------------------
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
root_dir = backend_dir.parent

for p in (str(root_dir), str(backend_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

# ------------------------------------------------------------------------------
# 2. Project Imports: Base, Settings, and all 10 registered models
# ------------------------------------------------------------------------------
try:
    from backend.config import settings
    from backend.database import Base
    import backend.models  # Imports Plant, ProductionLine, Machine, Sensor, TelemetryEvent,
                           # OperatingShift, MaintenanceWorkOrder, FailureEvent, Part,
                           # machine_parts, Technician
except ImportError:
    from config import settings
    from database import Base
    import models

# ------------------------------------------------------------------------------
# 3. Alembic Configuration
# ------------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for 'autogenerate' support
target_metadata = Base.metadata

# Inject the database URL from settings dynamically without hardcoding in alembic.ini
# Escape any '%' characters for ConfigParser interpolation
safe_url = settings.DATABASE_URL.replace("%", "%%")
config.set_main_option("sqlalchemy.url", safe_url)


# ------------------------------------------------------------------------------
# 4. Migration Modes (Offline and Online)
# ------------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Configures the context with just a URL and not an Engine, generating SQL scripts.
    """
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    Uses the existing project connection settings to connect directly to PostgreSQL.
    """
    try:
        from backend.database import engine as db_engine
    except ImportError:
        from database import engine as db_engine

    if db_engine is not None:
        connectable = db_engine
    else:
        connectable = create_engine(
            settings.DATABASE_URL,
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
