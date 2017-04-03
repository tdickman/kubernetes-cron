import json
import requests
import ssl
import websocket


class Manager(object):
    def __init__(self, base_url, headers=None, ca_cert=None):
        self.base_url = base_url
        self.headers = headers if headers else {}
        self.ca_cert = ca_cert

    def _watch(self, endpoint):
        ws = websocket.create_connection('{}{}?watch=true'.format(self.base_url, endpoint), header=self.headers, sslopt={'cert_reqs': ssl.CERT_OPTIONAL, 'ca_certs': self.ca_cert, 'check_hostname': False})
        for message in ws:
            yield json.loads(message)

    def _watch_http(self, endpoint):
        import time  # noqa
        while True:
            resp = requests.get('{}{}'.format(self.base_url.replace('wss:', 'http:'), endpoint), headers=self.headers)
            for item in resp.json()['items']:
                yield item
            time.sleep(20)

    def _post(self, endpoint, data):
        return requests.post('{}{}'.format(self.base_url.replace('wss:', 'http:'), endpoint), json=data, headers=self.headers)
