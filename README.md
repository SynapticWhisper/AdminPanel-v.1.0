# Authorization Service

This project is an authorization service built with FastAPI. It includes two-factor authentication (2FA) via email and uses JinjaTemplates for rendering.

## Setup Instructions

1. **Make the `pre_start.sh` script executable:**

   ```bash
   chmod +x scripts/pre_start.sh
   ```

2. **Run the pre-start script:**

   ```bash
   ./scripts/pre_start.sh
   ```
   
3. **Start the Redis container:**

   ```bash
   docker run --name RedisAPanel -d redis:latest
   ```
   
4. **Start the PostgreSQL container:**

   ```bash
   docker run --name APanelDB -p 5432:5432 -e POSTGRES_USER=<DB user> -e POSTGRES_PASSWORD=<DB password> -e POSTGRES_DB=<db name> -d postgres:16.4
   ```
   
5. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```
   
6. **Apply database migrations:**

   ```bash
   alembic upgrade head
   ```
   
7. **Start the FastAPI application:**

   ```bash
   uvicorn src.main:app --reload
   ```
   
8. **Start Celery worker:**

   ```bash
   celery -A src.tasks.mailing:celery worker --loglevel=info
   ```
   
9. **Start Celery Flower for monitoring:**

   ```bash
   celery -A src.tasks.mailing:celery flower
   ```

## Docker Compose
Docker Compose setup is coming soon!


## Features
* FastAPI for the main application framework.
* Two-factor authentication via email.
* JinjaTemplates for rendering HTML templates.
* Redis and PostgreSQL for caching and data storage.
* Celery for task management and asynchronous processing.

## Contribution
Feel free to open issues or submit pull requests if you have suggestions or improvements.

## License
This project is licensed under the MIT License, feel free to modify or expand as needed!
