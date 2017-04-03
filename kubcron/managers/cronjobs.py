from kubcron.managers import Manager


class CronJobManager(Manager):
    """Listens to the kubernetes api and updates its internal state as new cron jobs are created."""
    def __init__(self, base_url, headers=None, ca_cert=None):
        self.cronjobs = {}
        super(self.__class__, self).__init__(base_url, headers=headers, ca_cert=None)

    @staticmethod
    def _clean(cronjob):
        """Remove a bunch of extraneous data from the cronjob metadata that will cause problems when creating a job."""
        cronjob['metadata'].pop('creationTimestamp', None)
        cronjob['metadata'].pop('selfLink', None)
        cronjob['metadata'].pop('resourceVersion', None)
        cronjob['metadata'].pop('uid', None)
        return cronjob

    def watch(self):
        """Start listening to the kubernetes api and updating state."""
        for message in self._watch('/apis/epicconstructions.com/v1alpha1/cronjobs'):
            obj = message['object']
            name = '{}_{}'.format(obj['metadata']['namespace'], obj['metadata']['name'])
            if message['type'] in ['ADDED', 'MODIFIED']:
                self.cronjobs[name] = self._clean(obj)
            elif message['type'] == 'DELETED':
                self.cronjobs.pop(name, None)

if __name__ == '__main__':
    cr = CronJobManager('wss://localhost:8001')
    cr.watch()
