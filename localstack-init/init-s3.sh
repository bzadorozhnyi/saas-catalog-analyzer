#!/bin/bash
set -e

create_bucket() {
  local bucket="$1"

  awslocal s3 mb "s3://$bucket"
  echo "S3 bucket '$bucket' created successfully"
}

create_bucket report-documents
