import copy
from crontab import CronTab
import logging
import time


class Scheduler(object):
    """Runs at a regular interval and checks if any jobs need to run."""
    def __init__(self, cronjob_manager, job_manager, interval_secs=30):
        """Initialize.

        Args:
        - interval_secs - the frequency at which the schedule should check for jobs that need to run. This should be set to a value < the minimum cron interval.
        """
        self._interval = interval_secs
        self._cronjob_manager = cronjob_manager
        self._job_manager = job_manager

    def start(self):
        while True:
            time.sleep(self._interval)
            for _, cronjob in self._cronjob_manager.cronjobs.items():
                if 'schedule' not in cronjob['spec']:
                    logging.warn('Cronjob missing required field `schedule`. Skipping {}'.format(cronjob['metadata']['name']))
                    continue
                schedule = CronTab(cronjob['spec']['schedule'])
                name = '{name}-{last_trigger}'.format(name=cronjob['metadata']['name'], last_trigger=int(schedule.previous(delta=False)))
                if self._job_exists(cronjob['metadata']['namespace'], name):
                    logging.info('Skipping execution of {}'.format(name))
                else:
                    self._trigger_job(cronjob, name)
                    logging.info('Triggering creation of daughter job {}'.format(name))

    def _job_exists(self, namespace, name):
        return '{}_{}'.format(namespace, name) in self._job_manager.jobs

    def _trigger_job(self, cronjob, name):
        """Trigger the creation of a new child job from the given cronjob object."""
        metadata = copy.deepcopy(cronjob['metadata'])
        metadata['name'] = name

        spec = cronjob['spec']['jobTemplate']['spec']

        if 'metadata' not in spec['template']:
            spec['template']['metadata'] = {}

        if 'labels' not in spec['template']['metadata']:
            spec['template']['metadata']['labels'] = {}

        spec['template']['metadata']['labels']['name'] = metadata['name']

        # Set a default restartPolicy
        spec['template']['spec']['restartPolicy'] = spec['template']['spec'].get('restartPolicy', 'OnFailure')
        job = {
            'apiVersion': 'batch/v1',
            'kind': 'Job',
            'metadata': metadata,
            'spec': spec
        }
        self._job_manager.create(cronjob['metadata']['namespace'], job)
