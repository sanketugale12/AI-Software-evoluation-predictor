import redis
import time
import subprocess

r = redis.Redis(host='localhost', port=6379, db=0)
print("Monitoring Redis queue 'analysis' and 'celery'...")

try:
    while True:
        analysis_len = r.llen('analysis')
        celery_len = r.llen('celery')
        print(f"Analysis: {analysis_len} | Celery: {celery_len}".ljust(50), end='\r', flush=True)
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
