#!/bin/bash
# Install/restore the hormuz-collector systemd service.
# /etc does not survive VM replacement; this script is the recovery path.
set -e
SRC=/home/hatch/workspace/hormuz-tracker/systemd/hormuz-collector.service
cp "$SRC" /etc/systemd/system/hormuz-collector.service
chmod +x /home/hatch/workspace/hormuz-tracker/run_collector.sh
systemctl daemon-reload
systemctl enable hormuz-collector
systemctl restart hormuz-collector
systemctl --no-pager status hormuz-collector | head -12
