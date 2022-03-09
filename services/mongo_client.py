from motor.motor_asyncio import AsyncIOMotorClient

from settings import Settings


class MongoClient(object):

    def __init__(self, collection="files"):
        self.__settings = Settings()
        self.client = AsyncIOMotorClient(self.__settings.mongo_dsn)
        self.db = self.client.files
        self.collection = self.db[collection]

    def __enter__(self):
        return self.collection

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.client.close()
