import config
import signal
import sys
import os
import json
import uuid
import pika
from subprocess import PIPE, run, Popen
import subprocess
from copy import deepcopy
from time import sleep
from celery import Celery, chain, group, chord, subtask
from celery.signals import task_success, task_failure
from kombu import Exchange, Queue

app2 = Celery('app2')
app2.conf.update(
    broker_url='amqp://' + config.RMQ_USER + ':' + config.RMQ_PASS + '@' + config.RMQ_HOST + ':' + config.RMQ_PORT + config.RMQ_VHOST,
    result_backend='redis://' + config.REDIS_HOST + '/0',
    task_queues=(
        Queue('app1', Exchange('default', type='direct'), routing_key=config.RMQ_SCHEDULER_QUEUE),
        Queue('app2', Exchange('default', type='direct'), routing_key=config.RMQ_DECIDER_QUEUE)
    )
)

# this helper function allows to cycle from the output of a single task and
# generate one or more chained tasks at one sweep (dynamic mapping)
@app2.task()
def dmap(it, callback, **kwargs):
    #print(self.request)
    print(f"ARGS: {it}")
    print(kwargs)
    # Map a callback over an iterator and return as a chain
    callback = subtask(callback).set(queue=kwargs['queue'])
    return chain(callback.clone([arg,]) for arg in it)()

@app2.task()
def run_task(*args):
    # simulate a real delay doing something
    sleep(config.TASK_DUMMY_WAIT)

    json_cmd = json.loads(args[-1])
    print("Task JSON: " + str(args[-1]))

    p = Popen(json_cmd['cmd'], shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    result = p.returncode
    
    #print "Return code: ", p.returncode
    #print out.rstrip(), err.rstrip()

    if result == 0:
        return result
    else:
        raise Exception(err.rstrip())

@task_success.connect(sender=run_task)
def task_success_run_task(sender=None, **kwargs):
    # get the sender's request so we can dump the pipeline id
    sreq = sender._get_request()

    if len(sreq.args) == 1:
        pipeline_task_id = json.loads(sreq.args[0])['pl_task_id']
    else:
        pipeline_task_id = json.loads(sreq.args[-1])['pl_task_id']
    
    filename = config.SHARED_DIR + "/" + pipeline_task_id + ".log"

    # create shared directory if it doesn't exist
    if not os.path.exists(config.SHARED_DIR):
        os.makedirs(config.SHARED_DIR)

    if os.path.exists(filename):
        try:
            f = open(filename, 'a')
            f.write(sreq.id + " SUCCEDED !\n")
            f.close()
        except Exception as e:
            print(sreq.id + " task log failed :-(")
            print(e)
        else:
            print(sreq.id + " task log written successfully !")

    print("From task_success_run_task => SUCCESS (pipeline id = " + pipeline_task_id + ")")

@task_failure.connect(sender=run_task)
def task_failure_run_task(sender=None, **kwargs):
    # get the sender's request so we can dump the pipeline id
    sreq = sender._get_request()

    #print(str(kwargs['args'][0]))

    if len(sreq.args) == 1:
        pipeline_task_id = json.loads(sreq.args[0])['pl_task_id']
    else:
        pipeline_task_id = json.loads(sreq.args[-1])['pl_task_id']

    filename = config.SHARED_DIR + "/" + pipeline_task_id + ".log"

    # create shared directory if it doesn't exist
    if not os.path.exists(config.SHARED_DIR):
        os.makedirs(config.SHARED_DIR)

    if os.path.exists(filename):
        try:
            f = open(filename, 'a')
            f.write("# " + sreq.id + " FAILED !\n\n")
            f.write(str(kwargs['args'][0]) + "\n\n")
            f.write(str(kwargs['einfo']) + "\n\n")
            f.close()
        except Exception as e:
            print(sreq.id + " task log failed :-(")
            print(e)
        else:
            print(sreq.id + " task log written successfully !")

    print("From task_failure_run_task => FAILED (pipeline id = " + pipeline_task_id + ")")
    