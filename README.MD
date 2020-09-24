# BQ Slots Scheduler
This project describes how to use servless components to schedule modifications to BQ Slot commitments.

Instructions here describe howto deploy the contents of the app-engine-sched/ folder. If you are interested in deploying the code as Cloud Functions instead, the sched_add_capacity/ and sched_del_capacity/ folders can be deployed as separate functions.


## Enable App Engine
    gcloud app create --region='us-central1'

## CREATE TASK QUEUE
    gcloud tasks queues create commit-delete-queue

## Deploy the app engine app
    cd app-engine-sched
    #update app.yaml with configuration details
    gcloud app deploy

## Grant BigQuery Resource admin to the app engine service account
    SERV_ACCT=`gcloud iam service-accounts list --format="value(email)" | grep appspot.gserviceaccount.com`
    gcloud projects add-iam-policy-binding $DEVSHELL_PROJECT_ID \
    --member="serviceAccount:${SERV_ACCT}" \
    --role='roles/bigquery.resourceAdmin'

## Create cron job with Cloud Scheduler
    #Schedule 100 extra slots at 9AM M-F, for 3 hours
    gcloud scheduler jobs create app-engine add-slots --schedule="* 9 * * 1,2,3,4,5" --http-method="POST" --relative-url="/add_capcity" --message-body='{"region":"US", "extra_slots":100,"minutes":180}'

## Set app engine firewall
    #Prevent access except by Cloud Scheduler and Cloud Tasks
    gcloud app firewall-rules update default --action=DENY