import base64
import hmac
import json
import logging

from services.upload_api_client import UploadApiClient
from services.file_service import FileService
from utils import create_hex_digest, request_logger
from aiostream import stream
from settings import Settings


class TaskService(object):
    def __init__(self):
        self.fs = FileService()
        self.api_client = UploadApiClient()
        self.__settings = Settings()

    async def process_file(self, file_id: str):
        file = await self.fs.get_file(file_id)

        chunk_id = 0
        async for chunk in self.fs.file_gen(file.get('path')):
            chunk_id += 1
            content_sha256 = create_hex_digest("BYNDER-APP", chunk)
            b64_chunk = base64.b64encode(chunk)
            response = self.api_client.upload_chunks(file_id=file_id,
                                                     chunk_id=chunk_id,
                                                     chunk_data=b64_chunk,
                                                     content_sha256=content_sha256
                                                     )
            request_logger(response)

    async def finalise_file(self, file_id: str, file_hash: str, body: dict):
        chunk_data = dict()
        async for id, chunk in stream.merge(self.fs.get_chunks(file_id),
                                            self.fs.get_child_chunks(
                                                file_id)).stream():
            chunk_data[id] = base64.b64decode(chunk)
        file = b''
        for item in sorted(chunk_data.items()):
            file += item[1]

        if not len(file) == body.get("fileSize"):
            logging.exception("Files didn't match in terms of size",
                              json.dumps(body))
            raise ValueError("Files didn't match in terms of size")
        if not hmac.compare_digest(file_hash,
                                   create_hex_digest("BYNDER-APP",
                                                     file)):
            logging.exception("File's content hex didn't match",
                              json.dumps(body))
            raise ValueError("File's content hex didn't match")

        async for i in self.fs.gen_upload_file_to_remote_server(
                self.__settings.remote_server_dsn,
                body.get("filename"),
                file):
            logging.debug("{} named file has been "
                          "streaming to the remote server {}".
                          format(body.get("filename"), i))
