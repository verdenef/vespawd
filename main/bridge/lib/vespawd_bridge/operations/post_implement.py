"""post_implement operation (§4.5)."""

from __future__ import annotations

from vespawd_bridge import codes
from vespawd_bridge.api.types import BridgeResult, PostImplementInput
from vespawd_bridge.operations.context import HandlerContext
from vespawd_bridge.recovery.engine import hints_for_codes


def handle_post_implement(
    ctx: HandlerContext, payload: PostImplementInput, correlation_id: str
) -> BridgeResult:
    result = ctx.base_result("post_implement", correlation_id)
    result.vedaws_task_id = payload.vedaws_task_id

    iterations = max(1, min(ctx.manifest.run_max_iterations, 3))
    last_exit = 0
    for _ in range(iterations):
        run_result = ctx.cli.run_dispatch()
        last_exit = run_result.exit_code
        if run_result.exit_code == 0:
            break

    if last_exit != 0:
        result.warnings.append("vedaws run reported worker failures")
        result.codes.append(codes.CLI_FAILED)
        if ctx.manifest.run_strict_mode:
            result.ok = False
            result.blockers.append("post_implement strict_mode: run failed")
            result.recovery = hints_for_codes(result.codes)
            return result

    result.ok = True
    result.codes.append(codes.OK)
    return result
