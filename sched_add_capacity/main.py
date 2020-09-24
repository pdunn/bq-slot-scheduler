import json
import datetime
import os
from google.cloud import tasks_v2
from google.cloud.bigquery.reservation_v1 import ReservationServiceClient
from google.cloud.bigquery.reservation_v1 import CapacityCommitment
from google.protobuf import timestamp_pb2

"""
env:
  delete_url="https://us-central1-my-test-project.cloudfunctions.net/delete_slot_capacity"
  delete_queue="projects/my-test-project/locations/us-central1/queues/commit-delete-queue"
  admin_project_id="my-test-project"
  max_slots = 1000

test payload
{
  "region":"US",
  "extra_slots":100,
  "minutes":5
}
"""

def add_capacity_request(request):
    request_json = request.get_json(silent=True)
    print("parsed json {}".format(request_json))

    admin_project_id = os.environ.get('admin_project_id', None)
    max_slots = int(os.environ.get('max_slots', 1000))
    queue = os.environ.get('delete_queue', None)
    url = os.environ.get('delete_url', None)

    print("retrieved environment variables")
    
    if not request_json:
        return "message body not properly formatted as json"

    if not (queue and url and admin_project_id):
        return "'admin_project_id', 'delete_queue', and 'delete_url' environment variables must be set"
    
    region = request_json['region']
    slots = int(request_json['extra_slots'])
    minutes = int(request_json['minutes'])

    commit = add_capacity(admin_project_id,
                          region,
                          slots,
                          max_slots)
    
    if commit:
        resp = launch_delete_task(admin_project_id,
                                  region,
                                  url,
                                  queue,
                                  commit.name,
                                  minutes)
        print(resp)
        return "Created a commitment {}; scheduled removal with {}".format(commit, resp)



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


def launch_delete_task(admin_project_id, region, url, queue, commit_id, minutes):
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
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url":url,
            "headers":{"Content-type":"application/json"},
            "body":payload_utf8
        }
    }

    response = client.create_task(request={"parent":queue, "task":task})
    return response




