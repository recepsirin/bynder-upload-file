import base64
import hmac
import json
import os
from unittest import TestCase, mock, skip

from fastapi.testclient import TestClient
from starlette import status
from app import app
from utils import create_hex_digest


class APITestCase(TestCase, TestClient):
    @staticmethod
    def _read_mock_data(name):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(dir_path,
                               'mock_files/{0}.json'.format(name))) as f:
            return json.loads(f.read())

    def get_access_token(self):
        access_token = self._read_mock_data("credentials")['access_token']
        return access_token

    def get_hash_key_and_its_contents(self):
        raw_content = os.urandom(1048576)  # 1MB
        b64_content = str(base64.b64encode(raw_content))
        hash_key = create_hex_digest("BYNDER-APP", raw_content)
        return hash_key, b64_content, raw_content


class PrepareEndpointTestCase(APITestCase):

    def setUp(self):
        self.client = TestClient(app)
        self._headers = {
            "Authorization": "Bearer {0}".format(self.get_access_token())
        }

    def test_unauthorized_authorized_request(self):
        response = self.client.post("/upload/prepare/", {"file_path": "a.zip"})
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

        response = self.client.post("/upload/prepare/", {"file_path": "a.zip"},
                                    headers=self._headers)
        self.assertNotEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    @skip
    def test_invalid_path_and_file(self):
        response = self.client.post("/upload/prepare/", {"file_path": "a.zip"},
                                    headers=self._headers)
        self.assertEqual(status.HTTP_422_UNPROCESSABLE_ENTITY,
                         response.status_code)

        with mock.patch('os.path.isfile', return_value=True):
            response = self.client.post("/upload/prepare/",
                                        json={"file_path": "foo.zip"},
                                        headers=self._headers)
            self.assertNotEqual(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                response.status_code)
    # TODO Add Tests


class UploadChunkEndpointTestCase(APITestCase):

    def setUp(self):
        self.client = TestClient(app)
        self._hash_key, self._file_content, self._raw_content = \
            self.get_hash_key_and_its_contents()
        self._headers = {
            "Authorization": "Bearer {0}".format(self.get_access_token()),
            "content-sha256": self._hash_key
        }

    def test_unprovided_header_hash(self):
        response = self.client.post("/upload/622673a898c4f87bd6eb537c/chunk/1",
                                    headers={
                                        "Authorization": "Bearer {0}".format(
                                            self.get_access_token())
                                    },
                                    json={"file_content": self._file_content})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIsNone(response.headers.get("content-sha256"))

    def test_validate_hash_within_endpoint(self):
        response = self.client.post("/upload/622673a898c4f87bd6eb537c/chunk/1",
                                    headers=self._headers,
                                    json={"file_content": self._file_content})
        self.assertTrue(hmac.compare_digest(self._hash_key,
                                            create_hex_digest("BYNDER-APP",
                                                              self._raw_content)))

# @TODO Add all scenarios here and also implement below finalise endpoint
