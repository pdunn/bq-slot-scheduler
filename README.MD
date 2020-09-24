# TO SETUP Deploy inside of the Reservations Admin Project

# CREATE TASK QUEUE
`gcloud tasks queues create commit-delete-queue`

# Deploy app engine
1. cd app-engine-sched
2. update app.yaml with configuration details
3. `gcloud app deploy`

# Create cron job with Clou Scheduler
`gcloud scheduler jobs create app-engine add-slots --schedule="* 9 * * 1,2,3,4,5" --http-method="POST" --message-body='{"region":"US", "extra_slots":100,"minutes":5}'`