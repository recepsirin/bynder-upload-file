import json
import logging
import requests
from collections import OrderedDict
from settings import Settings


class UploadApiClient(object):

    def __init__(self):
        self.__settings = Settings()
        self.base_url = self.__settings.upload_api_base_url
        self.auth_url = "{}/auth/token/".format(self.base_url)
        self.username = self.__settings.upload_api_username
        self.password = self.__settings.upload_api_password
        self.session = None
        self.session_timeout = 60
        self.access_token = None

    def _request(self, url, data=None, method="POST", **kwargs):
        if self.session is None:
            self.session = requests.Session()

        if not self.access_token:
            self.authenticate()

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            'Authorization': 'Bearer {0}'.format(
                self.access_token)
        }

        content_header = kwargs.get("content_sha256")
        if content_header:
            headers.update({"content-sha256": content_header})

        r = requests.Request(method, url=url, data=data, headers=headers)

        prepared_req = r.prepare()

        result = self.session.send(prepared_req, timeout=self.session_timeout)
        result.raise_for_status()

        return result

    def _post(self, url, data, **kwargs):
        return self._request(url=url, data=data, method="POST", **kwargs)

    def authenticate(self):
        data = OrderedDict()
        data["username"] = self.username
        data["password"] = self.password
        response = requests.post(self.auth_url, data=data)

        try:
            response.raise_for_status()
        except Exception as e:
            logging.exception(e)
            raise e

        self.access_token = response.json().get("access_token")

    def upload_chunks(self, file_id, chunk_id, chunk_data, **kwargs):
        response = self._post(
            "{}/upload/{}/chunk/{}".format(self.base_url, file_id, chunk_id),
            data=json.dumps({"file_content": chunk_data.decode("utf-8")}),
            **kwargs)
        return response

    def finalise(self):
        # @TODO Implement finalise endpoint
        pass
