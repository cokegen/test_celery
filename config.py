import os

RMQ_HOST = 'localhost' if os.environ.get('RMQ_HOST') == None else 'rabbitmq'
RMQ_PORT = '5672'
RMQ_VHOST = '/'
RMQ_USER = 'root'
RMQ_PASS = 'pass1234'
RMQ_SCHEDULER_QUEUE = 'pipeline_scheduler'
RMQ_DECIDER_QUEUE = 'task_scheduler'

REDIS_HOST = 'localhost' if os.environ.get('REDIS_HOST') == None else 'redis'

SHARED_DIR = '/tmp/shared'
TASK_DUMMY_WAIT = 4
