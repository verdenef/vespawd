"""AI-backed executable worker base class."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Mapping

from vedaws.ai.capabilities import STANDARD_AI_CAPABILITIES
from vedaws.ai.model import GenerateRequest, GenerateResponse
from vedaws.ai.service import AIService
from vedaws.workers.execution import TaskDispatch, TaskOutcome
from vedaws.workers.interface import ExecutableWorker
from vedaws.workers.models import WorkerCapability, WorkerHealthReport, WorkerMetadata
from vedaws.workers.status import WorkerHealth, WorkerStatus
from vedaws.workers.types import WorkerType


class AIExecutableWorker(ExecutableWorker):
    """Base class for workers that execute tasks via AIService."""

    def __init__(
        self,
        *,
        worker_id: str,
        name: str,
        description: str,
        capabilities: tuple[str, ...],
        provider: str,
        source_path: Path | None = None,
        ai_service: AIService | None = None,
        ai_capability: str = "",
    ) -> None:
        self._ai_service = ai_service
        self._ai_capability = ai_capability.strip()
        self._skills: dict[str, tuple[str, str]] = {}
        self._metadata = WorkerMetadata(
            id=worker_id,
            name=name,
            description=description,
            version="0.1.0",
            worker_type=WorkerType.AI,
            capabilities=tuple(
                WorkerCapability(work_type=capability, scope="ai")
                for capability in capabilities
            ),
            status=WorkerStatus.AVAILABLE,
            provider=provider,
            source_path=source_path,
        )

    @property
    def metadata(self) -> WorkerMetadata:
        return self._metadata

    @property
    def ai_service(self) -> AIService | None:
        return self._ai_service

    def bind_ai_service(self, service: AIService) -> None:
        self._ai_service = service

    def bind_skills(self, skills: Mapping[str, tuple[str, str]]) -> None:
        self._skills = {
            str(skill_id): (str(name), str(description))
            for skill_id, (name, description) in skills.items()
            if str(skill_id).strip()
        }

    def health_check(self) -> WorkerHealthReport:
        if self._ai_service is None:
            return WorkerHealthReport(
                worker_id=self.id,
                health=WorkerHealth.DEGRADED,
                message="AI worker not wired to AIService",
            )
        return WorkerHealthReport(
            worker_id=self.id,
            health=WorkerHealth.HEALTHY,
            message="AI worker ready",
        )

    def _set_status(self, status: WorkerStatus) -> None:
        self._metadata = replace(self._metadata, status=status)

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        if self._ai_service is None:
            return TaskOutcome.failure(
                "AIService is not configured for this worker",
                task_key=dispatch.key,
                worker_id=self.id,
            )

        ai_capability = self._resolve_ai_capability(dispatch)
        if not ai_capability:
            return TaskOutcome.failure(
                f"Task '{dispatch.key}' does not map to a standard AI capability",
                task_key=dispatch.key,
                worker_id=self.id,
            )

        prompt = self.build_prompt(dispatch)
        request = GenerateRequest(
            prompt=prompt,
            capability=ai_capability,
            metadata={"task_key": dispatch.key, "worker_id": self.id},
        )
        try:
            response = self._generate_with_fallback(request)
        except RuntimeError as exc:
            return TaskOutcome.failure(str(exc), task_key=dispatch.key, worker_id=self.id)
        except Exception as exc:  # noqa: BLE001
            return TaskOutcome.failure(
                f"AI execution failed: {exc}",
                task_key=dispatch.key,
                worker_id=self.id,
            )

        content = response.content.strip()
        if not content:
            return TaskOutcome.failure(
                "AI provider returned empty content",
                task_key=dispatch.key,
                worker_id=self.id,
                ai_capability=ai_capability,
            )

        return TaskOutcome.success(
            message=f"AI task completed: {dispatch.key}",
            task_key=dispatch.key,
            worker_id=self.id,
            capability=dispatch.task.capability,
            ai_capability=ai_capability,
            provider_id=response.provider_id,
            model=response.model,
            content=content,
        )

    def build_prompt(self, dispatch: TaskDispatch) -> str:
        lines = [
            "You are executing one bounded task in Vedaws.",
            f"Task: {dispatch.task.name}",
        ]
        if dispatch.task.description:
            lines.append(f"Description: {dispatch.task.description}")
        if dispatch.instructions:
            lines.append(f"Instructions: {dispatch.instructions}")
        resolved_skills = self._resolve_skill_guidance(dispatch)
        if resolved_skills:
            lines.append("Skills guidance:")
            for skill_name, skill_description in resolved_skills:
                if skill_description:
                    lines.append(f"- {skill_name}: {skill_description}")
                else:
                    lines.append(f"- {skill_name}")
        lines.append("Stay in scope. If context is missing, state assumptions clearly.")
        return "\n".join(lines)

    def _resolve_ai_capability(self, dispatch: TaskDispatch) -> str:
        task_capability = dispatch.task.capability.strip()
        ai_capability = dispatch.task.ai_capability.strip()
        if ai_capability in STANDARD_AI_CAPABILITIES:
            return ai_capability
        if task_capability in STANDARD_AI_CAPABILITIES:
            return task_capability
        if self._ai_capability in STANDARD_AI_CAPABILITIES:
            return self._ai_capability
        return ""

    def _generate_with_fallback(self, request: GenerateRequest) -> GenerateResponse:
        if self._ai_service is None:
            raise RuntimeError("AIService is not configured")
        chain = self._ai_service.resolve_chain(request.capability)
        if not chain:
            raise RuntimeError(
                f"No AI provider available for capability '{request.capability}'"
            )
        last_error: Exception | None = None
        for provider in chain:
            try:
                response = provider.generate(request)
                if not response.provider_id:
                    return GenerateResponse(
                        content=response.content,
                        provider_id=provider.id,
                        model=response.model,
                        metadata=response.metadata,
                    )
                return response
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        if last_error is not None:
            raise RuntimeError(
                f"All providers failed for capability '{request.capability}': {last_error}"
            ) from last_error
        raise RuntimeError(f"No AI provider available for capability '{request.capability}'")

    def _resolve_skill_guidance(self, dispatch: TaskDispatch) -> list[tuple[str, str]]:
        resolved: list[tuple[str, str]] = []
        for skill_id in dispatch.task.skills:
            skill = self._skills.get(skill_id)
            if skill is None:
                continue
            resolved.append(skill)
        return resolved
