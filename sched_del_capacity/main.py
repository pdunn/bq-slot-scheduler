import json
from google.api_core import retry
from google.cloud.bigquery.reservation_v1 import ReservationServiceClient

"""
{
 "commit_id":"projects/{}/locations/US/capacityCommitments/7161799642806938531"
}
"""

def delete_capacity_request(request):
    print("received_request")
    request_json = request.get_json(silent=True)
    print("request body {}".format(request_json))

    commit_id = request_json['commit_id']
    
    client = ReservationServiceClient()
    client.delete_capacity_commitment(name=commit_id)
    return "removed {}".format(commit_id)

