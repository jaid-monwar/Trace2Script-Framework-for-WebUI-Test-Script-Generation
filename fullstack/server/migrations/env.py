from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.config import DATABASE_URL
from sqlmodel import SQLModel
import importlib
import pkgutil

def import_all_models():
    models_package = 'src.api.models'
    
    try:
        package = importlib.import_module(models_package)
        
        package_path = package.__path__
        
        for importer, modname, ispkg in pkgutil.iter_modules(package_path):
            if not ispkg and modname != '__init__':
                full_module_name = f"{models_package}.{modname}"
                importlib.import_module(full_module_name)
                print(f"Imported model module: {full_module_name}")
                
    except Exception as e:
        print(f"Error importing models: {e}")
        from src.api.models.user import User
        from src.api.models.task import Task
        from src.api.models.result import Result

import_all_models()

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata



def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()