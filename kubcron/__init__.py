# from crontab import CronTab
import gevent
import gevent.monkey
from gevent.lock import Semaphore
import json
from kubernetes import client, config, watch


# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()
sem = Semaphore()


class Monitor(object):
    def __init__(self):
        self._v1 = client.BatchV1Api()
        self._cron_jobs = {}
        self._child_jobs = {}

    def start(self):
        gevent.monkey.patch_all(select=False)
        # Force python to completely exit on any exception
        gevent.get_hub().SYSTEM_ERROR += (BaseException, )
        t2 = gevent.spawn(self._process_cron)
        t1 = gevent.spawn(self._process_events)
        gevent.joinall([t1, t2])

    def _trigger(self, job, timestamp):
        job = self._clean_job(job)
        job.metadata.name = '{}-{}'.format(job.metadata.name, timestamp)
        job.metadata.annotations['kubecron'] = json.dumps({
            'base_job': job.metadata.name,
            'timestamp': timestamp
        })
        self._v1.create_namespaced_job(job.metadata.namespace, job)

    def _process_events(self):
        w = watch.Watch()
        for event in w.stream(self._v1.list_job_for_all_namespaces):
            print("Event: %s %s" % (event['type'], event['object'].metadata.name))

            job = event['object']
            if job.metadata.name == 'southwest-alerts':
                continue
            if not job.metadata.annotations:
                continue
            if job.metadata.annotations.get('cron'):
                self._handle_cron_job(event['type'], job)
            elif job.metadata.annotations.get('kubecron'):
                self._handle_child_job(event['type'], job)

    def _handle_cron_job(self, event_type, job):
        print('handle_cron_job')
        namespaced_name = '{namespace}/{name}'.format(namespace=job.metadata.namespace, name=job.metadata.name)
        if event_type in ['ADDED', 'MODIFIED']:
            self._cron_jobs[namespaced_name] = (job, CronTab(job.metadata.annotations['cron']))
        elif event_type in ['DELETED']:
            del self._cron_jobs[namespaced_name]

    def _handle_child_job(self, event_type, job):
        print('handle_child_job')
        kubecron_values = json.loads(job.metadata.annotations['kubecron'])
        namespaced_name = '{namespace}/{name}'.format(namespace=job.metadata.namespace, name=kubecron_values['base_job'])
        if namespaced_name not in self._child_jobs:
            self._child_jobs[namespaced_name] = set()
        if event_type in ['ADDED', 'MODIFIED']:
            self._child_jobs[namespaced_name].add(kubecron_values['timestamp'])
        elif event_type in ['DELETED']:
            self._child_jobs[namespaced_name].remove(kubecron_values['timestamp'])

    def _process_cron(self):
        """Watch jobs with the cron annotation, and create child jobs based on the specified cron schedule."""
        while True:
            gevent.sleep(10)
            for name, (job, schedule) in self._cron_jobs.items():
                print(name)
                last_trigger = int(schedule.previous(delta=False))
                if last_trigger not in self._child_jobs.get(name, set()):
                    self._trigger(job, last_trigger)


if __name__ == '__main__':
    monitor = Monitor()
    monitor.start()
