import config
import signal
import sys
import os
import json
import uuid
import pika
from subprocess import PIPE, run
from copy import deepcopy
from time import sleep
from celery import Celery, chain, group, chord, subtask
from celery.signals import task_success, task_failure
from kombu import Exchange, Queue

app1 = Celery('app1')
app1.conf.update(
    broker_url='amqp://' + config.RMQ_USER + ':' + config.RMQ_PASS + '@' + config.RMQ_HOST + ':' + config.RMQ_PORT + config.RMQ_VHOST,
    result_backend='redis://' + config.REDIS_HOST + '/0',
    task_queues=(
        Queue('app1', Exchange('default', type='direct'), routing_key=config.RMQ_SCHEDULER_QUEUE),
        Queue('app2', Exchange('default', type='direct'), routing_key=config.RMQ_DECIDER_QUEUE)
    )
)

@app1.task(bind=True)
def process_pipeline(self, pipeline_json):
    print(self.request.id + " is the pipeline id to be generated ...")

    tl = {}
    
    for k, v in pipeline_json['tasks'].items():
        tv = str(v['parent'].strip('node_'))
        
        if tv != "":
            tl[int(tv)] = k
        else:
            tl[0] = k
    
    stasks = dict(sorted(tl.items()))

    pcopy = deepcopy(pipeline_json)

    try:
        del pcopy['tasks']
    except KeyError:
        pass

    pcopy['tasks'] = {}
    
    for k, v in stasks.items():
        pcopy['tasks'][v] = {}
        pcopy['tasks'][v] = pipeline_json['tasks'][v]

    jlist = []

    for ki, vi in pcopy['tasks'].items():
        vi["tname"] = ki
        vi["pl_task_id"] = self.request.id
        jlist.append(json.dumps(vi))
    
    return jlist

@task_success.connect(sender=process_pipeline)
def task_success_process_pipeline(sender=None, **kwargs):
    print(sender.request.id + " pipeline generation succeeded !")

    filename = config.SHARED_DIR + "/" + sender.request.id + ".log"

    # create shared directory if it doesn't exist
    if not os.path.exists(config.SHARED_DIR):
        os.makedirs(config.SHARED_DIR)

    if not os.path.exists(filename):
        try:
            f = open(filename, 'w')
            f.write("### pipeline contents\n\n" + str(kwargs['result']) + "\n\n")
            f.close()
        except Exception as e:
            print(sender.request.id + " pipeline log failed :-(")
            print(e)
        else:
            print(sender.request.id + " pipeline log written successfully !")
