# API Reference

This section is auto-generated from **docstrings** via `mkdocstrings` (`properdocs.yml: mkdocstrings.handlers.python` with `sys.path.append(".")`). Source lives in `app/`.

> **Setup**: `uv run properdocs serve` resolves `app.*` imports. If you add a new module, expose it here.

---

## Orchestrator

::: app.services.pymonitor.PyMonitor
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

---

## Metrics

### Service

::: app.services.metrics.MetricsService
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Decorator

::: app.services.metrics.monitor_metric
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

---

## Agent & Remediation

::: app.services.pyagent.PyAgent
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

---

## Messaging

### Messenger

::: app.services.messenger.MessengerService
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Telegram Interface

::: app.services.interfaces.TelegramInterface
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: app.services.interfaces.MessageInterface
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

---

## Alarms

::: app.services.alarm.AlarmService
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

---

## State

### Interface

::: app.services.database.DataBaseConnector
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### In-Memory Implementation

::: app.services.database.StateManager
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

---

## Models

### Event

::: app.models.event.Event
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Message

::: app.models.message.Message
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Request

::: app.models.request.Request
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

---

## Settings

::: app.settings.AppSettings
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: app.settings.TobiiSettings
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: app.settings.TelegramSettings
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: app.settings.MonitoringSettings
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: app.settings.AlarmSettings
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: app.settings.RemoteAccessSettings
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

---

## Logging

::: app.services.log.get_logger
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3
