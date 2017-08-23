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
            self._iteration()

    def _iteration(self):
        for cronjob in self._cronjob_manager.cronjobs.values():
            if 'schedule' not in cronjob['spec']:
                logging.warn('Cronjob missing required field `schedule`. Skipping {}'.format(cronjob['metadata']['name']))
                continue
            schedule = CronTab(cronjob['spec']['schedule'])
            last_trigger_time = int(schedule.previous(delta=False))
            cronjob_name = cronjob['metadata']['name']
            name = '{name}-{last_trigger}'.format(name=cronjob_name, last_trigger=last_trigger_time)
            status = cronjob.get('status', {'lastTrigger': 0})
            if status['lastTrigger'] >= last_trigger_time:
                logging.debug('Skipping execution of {} (status: {} previous schedule: {})'.format(
                    name, status['lastTrigger'], last_trigger_time))
            else:
                status['lastTrigger'] = last_trigger_time
                logging.info('Triggering creation of daughter job {}'.format(name))
                self._trigger_job(cronjob, name)
                cronjob['status'] = status
                logging.info('Triggering update of parent CronJob {}'.format(cronjob_name))
                self._cronjob_manager.update(cronjob)

    def _trigger_job(self, cronjob, name):
        """
        Trigger the creation of a new child job from the given cronjob object.
        Assumes the following:
        - The CronJob has a set .metadata field.
        - The CronJob has a set .spec.jobTemplate.spec.template.spec field.
        """
        cronjob_metadata = self._cleaned_metadata(cronjob['metadata'])
        cronjob_metadata['name'] = name

        job_spec = cronjob['spec']['jobTemplate']['spec']
        job_metadata = job_spec.setdefault('template', {'metadata': {}})
        job_labels = job_metadata.setdefault('labels', {})

        job_labels['name'] = cronjob_metadata['name']

        # Set a default restartPolicy
        job_spec['template']['spec'].setdefault('restartPolicy', 'OnFailure')
        job = {
            'apiVersion': 'batch/v1',
            'kind': 'Job',
            'metadata': cronjob_metadata,
            'spec': job_spec
        }
        self._job_manager.create(cronjob['metadata']['namespace'], job)

    @staticmethod
    def _cleaned_metadata(original):
        """Remove a bunch of extraneous data from the cronjob metadata that will cause problems when creating a job."""
        metadata = copy.deepcopy(original)
        metadata.pop('creationTimestamp', None)
        metadata.pop('selfLink', None)
        metadata.pop('resourceVersion', None)
        metadata.pop('uid', None)
        return metadata
