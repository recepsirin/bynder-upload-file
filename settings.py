from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "File Uploader"
    mongo_dsn: str = "mongodb://localhost:27017"
    redis_dsn: str = "redis://localhost:6379/0"
    upload_api_base_url: str = "http://127.0.0.1:8000"
    upload_api_username: str = "integration"
    upload_api_password: str = "Itest12345***"
    remote_server_dsn: str = ""  # full path to upload the file
