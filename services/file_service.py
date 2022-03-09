import logging
import mimetypes
import os

import aiofiles
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import WriteError
from fastapi import HTTPException
from starlette import status

from services.mongo_client import MongoClient


class FileService(object):
    def __init__(self):
        self._mongo_client = MongoClient()

    async def prepare_upload_operation(self, name: str, path: str, size: int,
                                       mimetype: str):
        result = await self._mongo_client.collection.insert_one({
            "name": name,
            "path": path,
            "size": size,
            "mimetype": mimetype,
            "chunks": []
        })
        return str(result._InsertOneResult__inserted_id)

    async def is_file_exist(self, file_id: str):
        try:
            file = await self._mongo_client.collection.find_one(
                {"_id": ObjectId(file_id)})
        except InvalidId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The file id is not in the valid format."
            )
        except Exception as e:
            logging.exception(e)
            raise e
        return True if file else False

    async def update_chunk(self, file_id: str, chunk_number: int, chunk: str):
        try:
            result = await self._mongo_client.collection.update_one(
                {"_id": ObjectId(file_id)},
                {"$push": {"chunks": {"id": chunk_number,
                                      "chunk": chunk}}

                 })
            return result
        except WriteError as we:
            if we.code == 17419:  # 16 MB Limit
                await self._mongo_client.collection.insert_one(
                    {
                        "parent_id": file_id,
                        "chunks": {"id": chunk_number,
                                   "chunk": chunk}
                    }
                )
        except Exception as e:
            logging.exception(e)

    @staticmethod
    def get_file_name(file_path: str):
        return os.path.basename(file_path)

    @staticmethod
    def get_mime_type(file_path: str):
        return mimetypes.guess_type(file_path)[0]

    @staticmethod
    def get_file_size(file_path: str):
        return os.path.getsize(file_path)

    async def file_gen(self, file_path: str):
        async with aiofiles.open(str(file_path), 'rb') as out_file:
            while content := await out_file.read(1048576):  # 1MB approximately
                yield content

    async def get_file(self, file_id: str):
        try:
            file = await self._mongo_client.collection.find_one(
                {"_id": ObjectId(file_id)})
        except InvalidId:
            raise ValueError("The file id is not in the valid format")
        except Exception as e:
            logging.exception(e)
            raise e
        return file

    async def get_chunks(self, file_id: str):
        file = await self.get_file(file_id)
        for i in file['chunks']:
            yield i['id'], i['chunk']

    async def get_child_chunks(self, file_id: str):
        chunks = self._mongo_client.collection.find({"parent_id": file_id})
        async for i in chunks:
            yield i['chunks']['id'], i['chunks']['chunk']

    async def gen_upload_file_to_remote_server(self, path: str, name: str,
                                               file_content):
        """
        :param str path: Exact directory path with the end of forward slash
        :param str name: Filename with its extension
        :param file_content: File's byte-formatted content combined in the task
        """
        try:
            async with aiofiles.open(os.path.join(path, name),
                                     "wb") as out_file:
                async with aiofiles.open(file_content, "rb") as file:
                    while content := await file.read(1048576):  # 1 MB chunk
                        yield out_file.write(content)
        except Exception as e:
            logging.debug(e)
