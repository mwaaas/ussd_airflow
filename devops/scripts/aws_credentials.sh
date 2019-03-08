#!/usr/bin/env bash

mkdir -p ~/.aws

cat > ~/.aws/config << EOL
[default]
output = json
region = eu-west-1
EOL

cat > ~/.aws/credentials << EOL
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}

EOL
