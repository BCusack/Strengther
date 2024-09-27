#!/bin/bash
STATUS=$(gcloud compute instances describe top-pair-server --zone=australia-southeast2-b --format="value(status)")
if [ "$STATUS" = "RUNNING" ]; then
  gcloud compute instances reset top-pair-server --zone=australia-southeast2-b
else
  echo "Instance is not in RUNNING state. Current state: $STATUS"
  echo "Please check the instance manually and restart if necessary."
  exit 1
fi
