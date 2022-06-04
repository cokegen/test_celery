
import config
import app1
import app2

if __name__ == '__main__':
    pl = {
        "name": "Analysis 1",
        "overall_status": "waiting",
        "tasks": {
            "node_2": {
                "cmd": "cd ~/results",
                "parent": "node_1",
                "status": "waiting"
            },
            "node_3": {
                "cmd": "cd ~/results ; echo 'HELLO WORLD!' > output.txt",
                "parent": "node_2",
                "status": "waiting"
            },
            "node_1": {
                "cmd": "cd ~ ; /bin/mkdir -p results",
                "parent": "",
                "status": "waiting"
            }
        }
    }
    
    # this is the workflow (celery canvas)
    workflow = (
        app1.process_pipeline.s(pl).set(queue=config.RMQ_SCHEDULER_QUEUE) |
        app2.dmap.s(app2.run_task.s(), queue=config.RMQ_DECIDER_QUEUE).set(queue=config.RMQ_DECIDER_QUEUE)
    ).apply_async()
