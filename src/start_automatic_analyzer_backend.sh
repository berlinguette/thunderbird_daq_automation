#!/bin/bash
PYFILE=automatic_analyzer_main.py
VENVDIR=../.venv

MONITOR_PATH=$(dirname "$0")
MONITOR_PATH=$( cd "$MONITOR_PATH" && pwd )

VENV_BIN_PATH=$MONITOR_PATH/$VENVDIR/bin

set -a && source .env.otel && source .env && set +a

if [ $# -eq 0 ]
    then
        ${VENV_BIN_PATH}/opentelemetry-instrument ${VENV_BIN_PATH}/python3 -u ${MONITOR_PATH}/${PYFILE}
    else
        ${VENV_BIN_PATH}/opentelemetry-instrument ${VENV_BIN_PATH}/python3 -u ${MONITOR_PATH}/${PYFILE} --envfile $1
fi
