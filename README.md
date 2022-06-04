# Test: Python + Celery

## :memo: How can I launch all this ?

### While being inside the test_celery directory:
Generate required directories that will be used by RabbitMQ and the apps to store required data:
```bash=1
mkdir -p datadirs/{rabbitmq,redis,shared}
```

Upgrading pip is optional (depends on your own environment)
```bash=2
pip install --upgrade pip
python3 -m venv venv/
source venv/bin/activate
pip install -r requirements
```

To start docker compose
```bash=6
docker compose up
```

Some flags to force build and recreate containers (optional)
```bash=7
docker compose up --build --force-recreate
```

Lastly, call a workflow
```bash=8
python3 run.py
```

After running the `run.py` script, just watch the activity from the `app1` (scheduler) and the `app2` (decider/worker) applications.

A local RabbitMQ will be available at http://localhost:15672/ and credentials are defined at the `.env` file.

The timezone the RabbitMQ, Redis and the apps will be using is also configured at the `.env` file with the `TIMEZONE` variable. On a systemd enabled machine one can check valid timezones with the following command: `timedatectl list-timezones`.

After successful (or not) runs for the pipelines, logs will be generated at the `datadir/shared` directory. The files here represent the UUID for the pipeline, and the contents of these files will have a copy of the pipeline tasks, along with the UUID's for the tasks and their result (either SUCCESS or FAILURE).
