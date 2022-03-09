import hashlib
import hmac
import logging


def create_hex_digest(key: str, msg: bytes) -> str:
    return hmac.new(bytes(key, "UTF-8"), msg, hashlib.sha256).hexdigest()


def request_logger(response):
    # @TODO Instantiate logging with AWS Cloud Watch Conf
    logging.debug("[Request] url: {}".format(response.request.url))
    logging.debug(
        "[Request] headers: {}".format(response.request.headers))
    logging.debug("[Request] body: {}".format(response.request.body))
    logging.debug(
        "[Request][Response] code: {}".format(response.status_code))
    logging.debug(
        "[Request][Response] content: {}".format(response.content))
