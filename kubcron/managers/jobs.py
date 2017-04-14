import logging

from kubcron.managers import Manager


class JobManager(Manager):
    """Listens to the kubernetes api and updates its internal state as new cron jobs are created."""
    def __init__(self, base_url, headers=None, ca_cert=None):
        self.jobs = {}
        super(self.__class__, self).__init__(base_url, headers=headers, ca_cert=None)

    def watch(self):
        """Start listening to the kubernetes api and updating state."""
        for message in self._watch('/apis/batch/v1/jobs'):
            obj = message['object']
            name = '{}_{}'.format(obj['metadata']['namespace'], obj['metadata']['name'])
            if message['type'] in ['ADDED', 'MODIFIED']:
                self.jobs[name] = obj
            elif message['type'] == 'DELETED':
                self.jobs.pop(name, None)

    def create(self, namespace, definition):
        resp = self._post('/apis/batch/v1/namespaces/{}/jobs'.format(namespace), definition)
        if resp.status_code != 201:
            logging.error(resp.text)
            raise Exception('Invalid status code {} received when creating job'.format(resp.status_code))
        return resp.json()


if __name__ == '__main__':
    j = JobManager('wss://localhost:8001')
    j.watch()
