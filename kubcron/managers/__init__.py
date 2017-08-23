import json
import requests
import ssl
import websocket


class Manager(object):
    def __init__(self, base_url, headers=None, ca_cert=None):
        self.base_url = base_url
        self.headers = headers if headers else {}
        self.ws_headers = [': '.join([key, value]) for key, value in self.headers.items()]
        self.ca_cert = ca_cert

    def k8s_watch(self, endpoint):
        # TODO: Get sslopt working with ssl.CERT_OPTIONAL
        ws = websocket.create_connection(
            '{}{}?watch=true'.format(self.base_url, endpoint),
            header=self.ws_headers, sslopt={'cert_reqs': ssl.CERT_NONE, 'ca_certs': self.ca_cert, 'check_hostname': False}
        )
        for message in ws:
            yield json.loads(message)

    def put(self, endpoint, data):
        return self._request(endpoint, data, requests.put)

    def post(self, endpoint, data):
        return self._request(endpoint, data, requests.post)

    def _request(self, endpoint, data, method=requests.post):
        return method(
            '{}{}'.format(self.base_url.replace('wss:', 'https:'), endpoint),
            json=data,
            headers=self.headers,
            verify=False
        )
