import json
import datetime
import os
from flask import Flask, request, render_template, jsonify
from google.cloud import tasks_v2
from google.cloud.bigquery.reservation_v1 import ReservationServiceClient
from google.cloud.bigquery.reservation_v1 import CapacityCommitment
from google.protobuf import timestamp_pb2


ROUTE_ADD_CAP="/add_capacity"
ROUTE_DEL_CAP="/del_capacity"

app = Flask(__name__)

@app.route(ROUTE_ADD_CAP, methods=['POST'])
def add_capacity_request():
    """
    {
        "region":"US",
        "extra_slots":100,
        "minutes":5
    }
    """
    request_json = request.get_json(force=True)
    print("parsed json {}".format(request_json))
    
    admin_project_id = os.environ.get('admin_project_id', None)
    max_slots = int(os.environ.get('max_slots', 1000))
    queue = os.environ.get('delete_queue', None)
    print("retrieved environment variables")
    
    if not request_json:
        return "message body not properly formatted as json"

    if not (queue and admin_project_id):
        return "'admin_project_id', 'delete_queue', and 'delete_url' environment variables must be set"
    
    region = request_json['region']
    slots = int(request_json['extra_slots'])
    minutes = int(request_json['minutes'])

    commit = add_capacity(admin_project_id,
                          region,
                          slots,
                          max_slots)
    
    if commit:
        print("created commitment {}".format(commit))
        resp = launch_delete_task(admin_project_id,
                                  region,
                                  queue,
                                  commit.name,
                                  minutes)
        return resp


@app.route(ROUTE_DEL_CAP, methods=['POST'])
def delete_capacity_request():
    print("received_request")
    request_json = request.get_json(force=True)
    print("request body {}".format(request_json))

    if not request_json:
        return "Unable to process request body"

    commit_id = request_json['commit_id']
    
    client = ReservationServiceClient()
    client.delete_capacity_commitment(name=commit_id)
    return "removed {}".format(commit_id)


def add_capacity(admin_project_id, region, extra_slots, max_slots):
    client = ReservationServiceClient()
    parent_arg = "projects/{}/locations/{}".format(admin_project_id, region)

    slots_to_add = check_project_slots(client, parent_arg, extra_slots, max_slots)

    if slots_to_add <= 0:
        return None
    
    commit_config = CapacityCommitment(plan='FLEX', slot_count=slots_to_add)
    commit = client.create_capacity_commitment(parent=parent_arg, 
                                               capacity_commitment=commit_config)

    return commit

    
def check_project_slots(client, parent_arg, extra_slots, max_slots):
    total = 0
    for commit in client.list_capacity_commitments(parent=parent_arg):
        total += commit.slot_count
    
    slot_cap = max_slots - extra_slots
    return min(extra_slots, slot_cap)


def launch_delete_task(admin_project_id, region, queue, commit_id, minutes):
    client = tasks_v2.CloudTasksClient()
    
    payload = {
        'commit_id':commit_id
    }
    payload_utf8 = json.dumps(payload).encode()

    d = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)
    timestamp = timestamp_pb2.Timestamp()
    timestamp.FromDatetime(d)

    task = {        
        "schedule_time":timestamp,
        'app_engine_http_request': {
            "http_method": tasks_v2.HttpMethod.POST,
            'relative_uri':ROUTE_DEL_CAP,
            #"headers":{"Content-type":"application/json"},
            "body":payload_utf8
        }
    }

    response = client.create_task(request={"parent":queue, "task":task})
    return response


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    #logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500


if __name__ == '__main__':
"""
    os.environ['admin_project_id'] = ''
    os.environ['max_slots'] = "1000"
    os.environ['delete_queue'] = "projects/{}/locations/us-central1/queues/{}"
"""
    app.run()


