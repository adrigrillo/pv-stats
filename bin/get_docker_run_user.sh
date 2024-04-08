#!/bin/bash

# =======================================
# Version: 1.0
# =======================================

docker run --rm --user "$(id -u)" -v "$PWD":/mount_test busybox sh -c "stat -c '%u' /mount_test"
