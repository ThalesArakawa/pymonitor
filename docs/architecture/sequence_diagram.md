# Sequence Flows

Two core flows drive PyMonitor. Both are `asyncio` queue-based and deduplicated on `Event.status` transitions.

---

## Active Monitoring - Detection, Remediation & Notification

Triggered every `check_interval` (default 10s) by each `@monitor_metric` poller. Only when `previous.status != current.status` does an `Event` leave the service.

```kroki-plantuml
@startuml
!theme materia
autonumber
skinparam shadowing false
skinparam roundcorner 8
skinparam DefaultFontName "Roboto"

actor "Windows OS" as OS
participant "MetricsService\n(@monitor_metric)" as MS
participant "StateManager" as SM
participant "event_queue\nasyncio.Queue" as EQ
participant "PyAgent\nactive_monitoring" as PA
participant "PyAgent\ntake_action" as TA
participant "Windows\nsc / taskkill" as WIN
participant "MessengerService" as MSG
participant "TelegramInterface" as TG
participant "AlarmService" as AL
participant "Caregiver\nTelegram App" as CG
participant "Speakers" as SPK

title Active Flow: Poll -> Detect -> Remediate -> Notify

loop every check_interval (default 10s) for each of 7 monitors
  MS -> OS : psutil / wmi query\n(locked_status, optikey_status, etc.)
  OS --> MS : raw data
  MS -> MS : build Event(message, status, value)\n+ enrich (event_id=uuid4, timestamp, resource_name)
  MS -> SM : get(resource_name)
  SM --> MS : previous Event(status)
  alt previous.status != current.status
    MS -> SM : update_state(resource_name, Event)
    MS -> EQ : put(Event)
  else no change
    MS -> MS : sleep(check_interval)
  end
end

EQ -> PA : get() [blocks until Event]
PA -> TA : take_action(Event)

alt resource_name == "Tobii_Services"
  TA -> WIN : to_thread(restart_tobii_service)\nsc stop/start Eyex/Tobii services
  WIN --> TA : bool success
else resource_name == "Optikey"
  TA -> WIN : taskkill -f -im OptiKey.exe\ncreate_subprocess_exec(path)
  WIN --> TA : bool success
else resource_name == "AnyDesk"
  TA -> WIN : taskkill -f -im AnyDesk.exe\ncreate_subprocess_exec(path)
  WIN --> TA : bool success
else no remediation
  TA --> PA : None
end

PA -> PA : create_message(Event) -> Message(content=Event.message)

par notify via Telegram
  PA -> MSG : send(Message)
  MSG -> TG : MessageInterface.send()
  TG -> TG : bot.send_message(chat_id, text, parse_mode=HTML)
  TG --> CG : HTML alert
else audible alarm (Charger, Tobii_Hardware only)
  PA -> AL : send_alarm(Event)
  AL -> AL : play_alarm(Event)
  alt status == False (failure)
    AL -> SPK : loop playsound(-nok.mp3)\nevery alarm.interval until cleared
  else status == True (recovered)
    AL -> SPK : playsound(-ok.mp3) once\n+ cancel loop
  end
end

note right of MS
  Decorator at app/services/metrics.py
  handles enrichment + diff + sleep.
  interval param currently ignored;
  always uses settings.monitoring.check_interval.
end note

note right of PA
  app/services/pyagent.py: active_monitoring
  runs gather(send + alarm) in parallel
end note
@enduml
```

**Files**: `app/services/metrics.py:7` (`monitor_metric`), `app/services/database.py:15` (`StateManager`), `app/services/pyagent.py:130` (`active_monitoring`), `app/services/alarm.py:20` (`send_alarm`).

---

## Passive Monitoring - Telegram Commands

The caregiver initiates this flow from any Telegram client.

```kroki-plantuml
@startuml
!theme materia
autonumber
skinparam shadowing false
skinparam roundcorner 8
skinparam DefaultFontName "Roboto"

actor "Caregiver" as CG
participant "Telegram\nBot API" as TAPI
participant "TelegramInterface\nlisten()" as TG
participant "request_queue\nasyncio.Queue" as RQ
participant "PyAgent\npassive_monitoring" as PP
participant "PyAgent\nrespond()" as RESP
participant "Filesystem\napp.log" as FS
participant "Webcam\ncv2" as CAM
participant "MessengerService" as MSG
participant "Telegram App" as TA

title Passive Flow: /log /photo Command

CG -> TAPI : /log  or  /photo  or  /status
TAPI -> TG : Update (polling)
activate TG

TG -> TG : CommandHandler matches\nget_log / get_photo / get_status
alt /log
  TG -> RQ : put(Request(message="log", update=Update))
else /photo and photo_mode==True
  TG -> RQ : put(Request(message="photo", update=Update))
else /status (stub)
  TG -> TG : logger.debug only
end
deactivate TG

RQ -> PP : get() [blocks]
PP -> RESP : respond(Request)

alt message == "photo"
  RESP -> CAM : get_photo()\nVideoCapture(0).read() -> imencode .jpeg
  CAM --> RESP : bytes | None
  RESP -> RESP : Message(type="photo", byte_content=bytes, recipient=Update)
else message == "log"
  RESP -> FS : get_log()\naiofiles.open(base_path/app.log, "rb").read()
  FS --> RESP : bytes
  RESP -> RESP : Message(type="doc", byte_content=bytes, recipient=Update)
else unknown
  RESP -> RESP : Message(content="Method not implemented!")
end

RESP --> PP : Message
PP -> MSG : send(Message)
MSG -> TG : interfaces[0].send(Message)

alt type == "photo"
  TG -> TAPI : reply_photo(byte_content)
else type == "doc"
  TG -> TAPI : reply_document(BytesIO, "application_log.txt")
else text
  TG -> TAPI : send_message(chat_id, HTML)
end

TAPI --> CG : Photo / Document / Text in chat

note right of TG
  app/services/interfaces.py:38 listen()
  polling retry: except TelegramError -> sleep 360s
  Handlers added at startup.
end note

note right of RESP
  app/services/pyagent.py:50 respond()
  recipient=Update allows reply_*;
  plain send uses chat_id fallback.
end note
@enduml
```

**Files**: `app/services/interfaces.py:38` (`listen`, `get_log`, `get_photo`), `app/services/pyagent.py:50` (`respond`, `get_photo`, `get_log`), `app/services/messenger.py:15` (`MessengerService`).

---

## Failure & Retry Notes

* **Telegram polling failure**: `TelegramInterface.listen` catches `TelegramError` (base for `NetworkError`, `InvalidToken`, `Conflict`, etc.) and sleeps 360s before retry - no crash.
* **Send failure**: `TelegramInterface.send` catches `TelegramError` and logs `Telegram error: {e}` - message is dropped, not requeued.
* **Poller isolation**: `MetricsService.start` uses `gather(*valid_methods)` where each method is an infinite loop; a single poller exception does not kill others (but currently no per-iteration try/except - see Roadmap).
* **Alarm cancellation**: `AlarmService` stores per-`resource_name` `asyncio.Event` + `Task`; a success `Event(status=True)` sets the event, cancelling the `-nok.mp3` loop.
