"""
Создать все таблицы в БД на основе моделей SQLAlchemy.
Запуск: python init_db.py
"""
from app.db.connection import engine
from app.db import models  # noqa: F401 — регистрирует модели в Base.metadata
from app.db.models import Base

def main():
    print("Таблицы, которые будут созданы:")
    for name in sorted(Base.metadata.tables.keys()):
        print(f"  - {name}")

    print("\nСоздаю таблицы...")
    Base.metadata.create_all(bind=engine)
    print("Готово.")

    # Проверка
    from sqlalchemy import inspect
    insp = inspect(engine)
    print("\nТаблицы в БД после создания:")
    for name in sorted(insp.get_table_names()):
        print(f"  - {name}")


if __name__ == "__main__":
    main()