import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
# We might not need Django for celery if we use lithium_core logic, 
# but if we share models, we rely on sqlalchemy.
# For this setup, we will configure Celery purely with config.

broker_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
result_backend = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery('lithium', broker=broker_url, backend=result_backend)

# Production configuration
app.conf.update(
    result_expires=86400, # 24 hours
    timezone='UTC',
    task_acks_late=True, # Task is acknowledged after execution
    task_reject_on_worker_lost=True, # Re-queue task if worker dies
    worker_prefetch_multiplier=1, # One task at a time per worker for long tasks
    task_time_limit=1800, # 30 min hard limit
    task_soft_time_limit=1500, # 25 min soft limit
)

@app.task
def debug_task():
    print('Request: Debug Task Executed')
