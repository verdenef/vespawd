"""System event type constants — extensible string identifiers."""


class EventType:
    PROJECT_INITIALIZED = "ProjectInitialized"
    PROJECT_STATE_CHANGED = "ProjectStateChanged"
    WORKFLOW_STARTED = "WorkflowStarted"
    WORKFLOW_COMPLETED = "WorkflowCompleted"
    TASK_CREATED = "TaskCreated"
    TASK_STARTED = "TaskStarted"
    TASK_COMPLETED = "TaskCompleted"
    TASK_FAILED = "TaskFailed"
    WORKER_REGISTERED = "WorkerRegistered"
    WORKER_STARTED = "WorkerStarted"
    WORKER_COMPLETED = "WorkerCompleted"
    PLUGIN_LOADED = "PluginLoaded"
    PLUGIN_UNLOADED = "PluginUnloaded"


SYSTEM_EVENT_TYPES: tuple[str, ...] = (
    EventType.PROJECT_INITIALIZED,
    EventType.PROJECT_STATE_CHANGED,
    EventType.WORKFLOW_STARTED,
    EventType.WORKFLOW_COMPLETED,
    EventType.TASK_CREATED,
    EventType.TASK_STARTED,
    EventType.TASK_COMPLETED,
    EventType.TASK_FAILED,
    EventType.WORKER_REGISTERED,
    EventType.WORKER_STARTED,
    EventType.WORKER_COMPLETED,
    EventType.PLUGIN_LOADED,
    EventType.PLUGIN_UNLOADED,
)
