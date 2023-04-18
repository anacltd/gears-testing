import logging
from json import JSONDecodeError

import requests

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)


class HttpError(Exception):
    pass


def _request(_session, method: str, path: str, **kwargs):
    """ Sends an HTTP request """
    try:
        response = _session.request(method, path, **kwargs)
        response.raise_for_status()
        try:
            results = response.json()
        except JSONDecodeError:
            results = response.content
    except requests.exceptions.HTTPError as http_error:
        response = http_error.response
        try:
            json_response = response.json()
            msg = json_response.get("msg") or json_response.get("error")
        except ValueError:
            msg = response.text or None
        logger.error(msg)
        raise HttpError(
            f'HTTP error {response.status_code} for request {method} {response.url} ({msg})') from http_error
    except ValueError:
        results = None
    return results
