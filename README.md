# NLP-to-Filters
Translate user query to set of filters on the UI

http://localhost:5001/health


http://localhost:5001/redis/health


http://localhost:8001/ 

```sh

docker compose build


# Запуск
docker compose up -d

# Остановка (БЕЗ удаления volumes)
docker compose down

# Перезапуск
docker compose restart

# Просмотр логов
docker compose logs redis

docker compose logs app



# Просмотр логов в реальном времени
# Для выхода из режима просмотра логов Ctrl+C.

docker compose logs -f redis

docker compose logs -f app

# Логи всех сервисов в реальном времени
docker compose logs -f

# Последние 50 строк + реальное время
docker compose logs -f --tail=50 app


# Выполнение команд в контейнерах
docker compose exec app python -m scripts.populate_redis

docker compose exec redis redis-cli keys "*"

```
