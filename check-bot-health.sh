#!/bin/bash
# Health check script for dreamstime-bot
# Automatically starts the bot if it's inactive

SERVICE="dreamstime-bot"
LOG_FILE="/home/ubuntu/Dreamstime-AutoUploader/health-check.log"

# Check if service is active
if ! systemctl is-active --quiet $SERVICE; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $SERVICE is inactive. Starting..." >> $LOG_FILE
    systemctl start $SERVICE
    sleep 2
    if systemctl is-active --quiet $SERVICE; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $SERVICE started successfully" >> $LOG_FILE
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Failed to start $SERVICE" >> $LOG_FILE
    fi
fi
