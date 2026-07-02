"""Machine-readable error and warning codes (§9.1)."""

OK = "ok"
VEDAWS_MISSING = "vedaws_missing"
MISSING_MANIFEST = "missing_manifest"
INVALID_MANIFEST = "invalid_manifest"
INVALID_PATH = "invalid_path"
LAYOUT_CONFLICT = "layout_conflict"
VERSION_MISMATCH = "version_mismatch"
BOOTSTRAP_FAILED = "bootstrap_failed"
DOCTOR_BLOCKED = "doctor_blocked"
DOCTOR_WARN = "doctor_warn"
DESIGN_GATE_BLOCKED = "design_gate_blocked"
DESIGN_GATE_OVERRIDDEN = "design_gate_overridden"
STATE_INELIGIBLE = "state_ineligible"
STATE_TRANSITION_DENIED = "state_transition_denied"
WORKFLOW_TASK_MISMATCH = "workflow_task_mismatch"
PHASE_MAP_MISS = "phase_map_miss"
TASK_COMPLETE_DENIED = "task_complete_denied"
ARTIFACTS_MISSING = "artifacts_missing"
ORCHESTRATION_OFFLINE = "orchestration_offline"
SYNC_INCOMPLETE = "sync_incomplete"
WORKFLOW_CORRUPT = "workflow_corrupt"
CLI_FAILED = "cli_failed"
CLI_TIMEOUT = "cli_timeout"
CLI_SPAWN_ERROR = "cli_spawn_error"
INTERNAL_ERROR = "internal_error"
PROJECTION_DRIFT_CORRECTED = "projection_drift_corrected"
HANDOFF_STALE = "handoff_stale"
RECOVERY_RETRY = "recovery_retry"
CLI_OK = "cli_ok"

BLOCKING_CODES = frozenset(
    {
        VEDAWS_MISSING,
        MISSING_MANIFEST,
        INVALID_MANIFEST,
        INVALID_PATH,
        LAYOUT_CONFLICT,
        VERSION_MISMATCH,
        BOOTSTRAP_FAILED,
        DOCTOR_BLOCKED,
        DESIGN_GATE_BLOCKED,
        STATE_INELIGIBLE,
        STATE_TRANSITION_DENIED,
        TASK_COMPLETE_DENIED,
        ARTIFACTS_MISSING,
        WORKFLOW_CORRUPT,
        CLI_FAILED,
        CLI_TIMEOUT,
        CLI_SPAWN_ERROR,
        INTERNAL_ERROR,
    }
)

WARNING_CODES = frozenset(
    {
        DOCTOR_WARN,
        DESIGN_GATE_OVERRIDDEN,
        WORKFLOW_TASK_MISMATCH,
        PHASE_MAP_MISS,
        ORCHESTRATION_OFFLINE,
        SYNC_INCOMPLETE,
        PROJECTION_DRIFT_CORRECTED,
        HANDOFF_STALE,
    }
)

INFO_CODES = frozenset({RECOVERY_RETRY, CLI_OK, OK})
