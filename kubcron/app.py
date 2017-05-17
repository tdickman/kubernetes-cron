import logging
import os
import sys
import threading

from kubcron.managers import cronjobs, jobs
from kubcron.scheduler import Scheduler


KUB_API_TOKEN = '/var/run/secrets/kubernetes.io/serviceaccount/token'
KUB_CA_CERT = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
KUB_API_HOST = os.environ['KUBERNETES_SERVICE_HOST']
KUB_API_PORT = os.environ['KUBERNETES_PORT_443_TCP_PORT']

# Setup a few variables for authenticating with the kubernetes api
with open(KUB_API_TOKEN, 'r') as f:
    kub_headers = {'Authorization': 'Bearer {}'.format(f.read())}


logging.basicConfig(level=logging.INFO)
cr = cronjobs.CronJobManager(
    'wss://{}:{}'.format(KUB_API_HOST, KUB_API_PORT),
    headers=kub_headers,
    ca_cert=KUB_CA_CERT
)
j = jobs.JobManager(
    'wss://{}:{}'.format(KUB_API_HOST, KUB_API_PORT),
    headers=kub_headers,
    ca_cert=KUB_CA_CERT
)
scheduler = Scheduler(cr, j)
t1 = threading.Thread(target=cr.watch)
t2 = threading.Thread(target=j.watch)
t3 = threading.Thread(target=scheduler.start)
t1.daemon = True
t2.daemon = True
t3.daemon = True
t1.start()
t2.start()
t3.start()


# Exit if any thread crashes
while True:
    t1.join(0.5)
    t2.join(0.5)
    t3.join(0.5)
    for t in [t1, t2, t3]:
        if not t.isAlive():
            logging.error('Thread crashed. Exiting.')
            sys.exit(1)
