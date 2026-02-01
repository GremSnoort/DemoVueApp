# Инструкция по подготовке окружения (Windows)

## 1. Установка PostgreSQL

### Версия

Принимаются версии PostgreSQL 16 / 17 / 18.

### Установка

- Скачать официальный установщик с сайта PostgreSQL.
- Установка стандартная, через GUI.
- В процессе установки обязательно задаётся пароль для пользователя postgres —
👉 этот пароль нужно сохранить, он потребуется для администрирования и подключения к БД.

### Важно

- После установки сервер БД уже запущен (`pg_ctl` running).
- Поднимать сервер вручную не требуется — PostgreSQL готов к работе сразу после установки.
- Готов стандартный суперпользователь `postgres`

### Пути

Бинарные файлы PostgreSQL находятся по пути (пример для версии 18):

```bash
C:\Program Files\PostgreSQL\18\bin
```

Рекомендуется либо:

- добавить этот путь в PATH,
- работать из этой директории при использовании `psql`, `pg_ctl` и др.

### Настройка user & database для **DEMOAPP**

Подключиться к серверу БД под стандартным admin user `postgres`:

```bash
psql -h 127.0.0.1 -p 5432 -U postgres -d postgres
```

Создать user & database (внутри `psql`):

```sql
-- создать роль с паролем
CREATE ROLE app WITH LOGIN PASSWORD 'app';

-- создать базу и сделать app владельцем
CREATE DATABASE app OWNER app;

-- дать все права на базу
GRANT ALL PRIVILEGES ON DATABASE app TO app;
```

Проверить подключение:

```bash
psql -h 127.0.0.1 -p 5432 -U app -d app
```

#### URL для подключения **DEMOAPP**

```bash
postgresql://app:app@127.0.0.1:5432/app?sslmode=disable
```
_____________________________________

## 2. Установка Python

### Версия

Python 3.x (актуальная стабильная версия).

### Установка

- Скачать официальный установщик с сайта python.org.
- Установить от имени администратора.
- Обязательно отметить галочку “Add Python to PATH”.

После установки Python доступен из командной строки:

```bash
python --version
```

### Виртуальное окружение (venv) **DEMOAPP**

Создание виртуального окружения в каталоге проекта:

```bash
python -m venv .venv
```

### Активация окружения для **DEMOAPP**

#### PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

#### CMD:

```bat
.venv\Scripts\Activate.bat
```

После активации в prompt появится префикс:

```bash
(.venv)
```

⚠️ Если PowerShell блокирует активацию (ExecutionPolicy), выполнить один раз:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## 3. Установка Node.js

### Версия

Использовать LTS-версию Node.js.

### Установка

- Скачать .msi установщик с официального сайта nodejs.org.
- Установка стандартная, через GUI.

После установки:

- доступна оболочка с настроенным окружением (через стандартный поиск Windows)
- `node` и `npm` доступны из командной строки
- `npm` готов к использованию без дополнительной настройки

Проверка:

```bat
node -v
npm -v
```

### Создание проекта (Vue + JS) **DEMOAPP**

Из основной папки проекта выполнить:

```bash
npm create vite@latest frontend -- --template vue
cd frontend
npm install
npm i axios
```

Создать `.env`:

```bash
cat > .env <<'EOF'
VITE_API_BASE_URL=http://localhost:8080/api
EOF
```
