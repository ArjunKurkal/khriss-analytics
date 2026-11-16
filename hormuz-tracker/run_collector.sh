#!/bin/bash
# Entry point for the hormuz-collector systemd service.
# Source the runtime egress profile (proxy + CA bundle): direct egress
# from this VM is blocked, and systemd does not inherit the agent
# shell's environment. The profile is runtime-provided; no proxy
# credential is stored in this repo.
if [ -f /etc/profile.d/hatch-egress.sh ]; then
  set -a
  . /etc/profile.d/hatch-egress.sh
  set +a
fi
exec /home/hatch/workspace/hormuz-tracker/.venv/bin/python \
  /home/hatch/workspace/hormuz-tracker/src/collector.py
