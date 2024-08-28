```bash
chmod +x scripts/pre_start.sh
./scripts/pre_start.sh
docker run --name RedisAPanel -d redis:latest
docker run --name APanelDB -p 5432:5432 -e POSTGRES_USER=<DB user> -e POSTGRES_PASSWORD=<DB password> -e POSTGRES_DB=<db name> -d postgres:16.4
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload
celery -A src.tasks.mailing:celery worker --loglevel=info
celery -A src.tasks.mailing:celery flower
```

Docker-compose comming soon!
