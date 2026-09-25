#!/bin/bash
set -e

create_queue_with_dlq() {
  local queue_name="$1"
  local dlq_name="$2"

  local dlq_url dlq_arn
  dlq_url=$(awslocal sqs create-queue --queue-name "$dlq_name" --query 'QueueUrl' --output text)
  dlq_arn=$(awslocal sqs get-queue-attributes --queue-url "$dlq_url" --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

  awslocal sqs create-queue --queue-name "$queue_name" --attributes "{\"VisibilityTimeout\":\"60\",\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$dlq_arn\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}"

  echo "SQS queues created: $queue_name (VisibilityTimeout=60s) + DLQ $dlq_name (maxReceiveCount=3)"
}

create_queue_with_dlq catalog-creation-queue catalog-creation-dlq
