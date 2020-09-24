# TO SETUP Deploy inside of the Reservations Admin Project

# CREATE TASK QUEUE
    gcloud tasks queues create commit-delete-queue

# Deploy the app engine app
    cd app-engine-sched
    #update app.yaml with configuration details
    gcloud app deploy

# Grant BigQuery Resource admin to the app engine service account
    SERV_ACCT=\`gcloud iam service-accounts list --format="value(email)" | grep appspot.gserviceaccount.com\`
    gcloud projects add-iam-policy-binding $DEVSHELL_PROJECT_ID \\
    --member="serviceAccount:${SERV_ACCT}" \\
    --role='roles/bigquery.resourceAdmin'


# Create cron job with Clou Scheduler
    gcloud scheduler jobs create app-engine add-slots --schedule="* 9 * * 1,2,3,4,5" --http-method="POST" --relative-url="/add_capcity" --message-body='{"region":"US", "extra_slots":100,"minutes":5}'