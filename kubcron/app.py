import threading
import logging
import sys

from kubcron.managers import cronjobs, jobs
from kubcron.scheduler import Scheduler


logging.basicConfig(level=logging.INFO)
cr = cronjobs.CronJobManager('wss://localhost:8001')
j = jobs.JobManager('wss://localhost:8001')
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


while True:
    t1.join(0.5)
    t2.join(0.5)
    t3.join(0.5)
    for t in [t1, t2, t3]:
        if not t.isAlive():
            logging.error('Thread crashed. Exiting.')
            sys.exit(1)
