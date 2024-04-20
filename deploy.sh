#!/bin/bash

# Set the server details
SERVER="ubuntu@got.jemavi.co"
REMOTE_PATH="/home/ubuntu/got/django_hivik"
LOCAL_PATH="C:\Users\medin\Desktop\django_hivik"
cd "$LOCAL_PATH"
git add .
git commit -m "$(date +"%Y-%m-%d %H:%M:%S")"
git push
ssh -i C:\Users\medin\Desktop\GOT-SERPORT.pem "$SERVER" "cd '$REMOTE_PATH' && git pull"
