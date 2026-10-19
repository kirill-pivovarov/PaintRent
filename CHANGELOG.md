# Changelog: Реализация API-слоя

### 1. Настроен конфиг и подключение к БД через Depends
- **`app/core/config.py`**: Добавлен класс `Settings` на базе `pydantic-settings` для чтения `.env` (сборка `DATABASE_URL` из разрозненных переменных).
- **`app/db/connection.py`**: Переведен на использование `settings`. Настроен асинхронный `engine` и фабрика сессий `AsyncSessionLocal`.
- **`app/api/deps.py`**: Реализована зависимость `get_db` (через `yield`) с автоматическим `commit` при успехе и `rollback` при ошибке.

### 2. Реализована JWT-аутентификация и регистрация пользователей
- **`app/core/security.py`**: Добавлены функции хеширования паролей (`pwdlib`) и генерации/валидации JWT-токенов (`python-jose`).
- **`app/schemas/`**: Созданы DTO `UserCreate`, `UserRead` (без пароля) и `Token`.
- **`app/api/deps.py`**: Добавлены зависимости `get_current_user` (достает юзера из токена) и фабрика `require_role` (проверка прав).
- **`app/api/v1/auth.py`** и **`app/main.py`**: Реализованы и подключены эндпоинты `POST /auth/register`, `POST /auth/login`, `GET /auth/me`.
- **phone_number -> phone**: во всех конфигурациях _(DB, model, CRUD, app/ и т.д.)_ теперь используется обозначение _phone_ для удобства.
