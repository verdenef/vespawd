"""PAWS synchronization writers (Executor Spec §5)."""

from vespawd_executor.sync.completed import write_completed_log
from vespawd_executor.sync.current_task import set_task_status
from vespawd_executor.sync.engine import sync_paws_files
from vespawd_executor.sync.handoff import HandoffFacts, handoff_facts_from_task, refresh_handoff
from vespawd_executor.sync.notes import append_task_note
from vespawd_executor.sync.progress_log import append_progress_entry
from vespawd_executor.sync.types import PawsSyncResult

__all__ = [
    "PawsSyncResult",
    "sync_paws_files",
    "append_progress_entry",
    "append_task_note",
    "write_completed_log",
    "set_task_status",
    "HandoffFacts",
    "handoff_facts_from_task",
    "refresh_handoff",
]
