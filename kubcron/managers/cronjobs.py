from kubcron.managers import Manager


class CronJobManager(Manager):
    API_PREFIX = '/apis/epicconstructions.com/v1alpha1/cronjobs'

    """Listens to the kubernetes api and updates its internal state as new cron jobs are created."""
    def __init__(self, base_url, headers=None, ca_cert=None):
        self.cronjobs = {}
        super(self.__class__, self).__init__(base_url, headers=headers, ca_cert=None)

    def update(self, obj):
        resp = self.put(obj['metadata']['selfLink'], obj)
        if resp.status_code == 409:
            logging.info('CronJob already exists. Skipping.')
        elif resp.status_code != 200:
            logging.error(resp.text)
            raise Exception('Invalid status code {} received when updating CronJob'.format(resp.status_code))

    def watch(self):
        """Start listening to the kubernetes api and updating state."""
        for message in self.k8s_watch(self.API_PREFIX):
            obj = message['object']
            name = '{}_{}'.format(obj['metadata']['namespace'], obj['metadata']['name'])
            if message['type'] in ['ADDED', 'MODIFIED']:
                self.cronjobs[name] = obj
            elif message['type'] == 'DELETED':
                self.cronjobs.pop(name, None)

if __name__ == '__main__':
    cr = CronJobManager('wss://localhost:8001')
    cr.watch()
