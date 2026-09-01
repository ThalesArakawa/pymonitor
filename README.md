# PyMonitor

Verifying Computer Status and, optionally, send to TelegramBot



To transform into a Exe, inside a root project, runs:

```bash
uv sync
```


```bash
uv run pyinstaller --name "PyMonitor" -p .\app\ main.py --noconsole --onefile
```

## Environment Variables

```bash
# Name of Optikey Executable (.exe)
PYMONITOR__TOBII__OPTIKEY_EXE_NAME=
# Full path to Executable
PYMONITOR__TOBII__OPTIKEY_PATH=
# Name of Tobii Engine Service Executable (.exe)
PYMONITOR__TOBII__EYEX_ENGINE_EXE_NAME=
# Name of Tobii Engine Interaction Executable (.exe)
PYMONITOR__TOBII__EYEX_INTERACTION_EXE_NAME=
# Name of Tobii Service Executable (.exe)
PYMONITOR__TOBII__SERVICE_EXE_NAME=
# Name of Tobii Service
PYMONITOR__TOBII__SERVICE_NAME=
# Name of Tobii Generic Service
PYMONITOR__TOBII__GENERIC_NAME=
# Name of Tobii Eyetracker Service
PYMONITOR__TOBII__EYETRACKER_NAME=

# TELEGRAM
PYMONITOR__USE_TELEGRAM=False
PYMONITOR__TELEGRAM__BOT_TOKEN=
PYMONITOR__TELEGRAM__CHAT_ID=

# # MONITORING SETTINGS
PYMONITOR__MONITORING__PHOTO_MODE=false
PYMONITOR__MONITORING__CHECK_INTERVAL=

# REMOTE ACCESS SETTINGS
PYMONITOR__REMOTE_ACCESS__ANYDESK_EXE_NAME=
PYMONITOR__REMOTE_ACCESS__ANYDESK_PATH=

# # ALARM SOUND
PYMONITOR__USE_ALARM_SOUND=true
```

## Read the Docs!

We are using properdocs to help construct the documentation