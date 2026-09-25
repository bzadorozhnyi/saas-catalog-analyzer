import asyncio
import uuid
from dataclasses import dataclass

import logfire

from app.ai.pricing import calculate_cost_usd
from app.db.session import async_session_factory
from app.enums.llm_call_purpose_enum import LlmCallPurposeEnum
from app.enums.llm_call_status_enum import LlmCallStatusEnum
from app.models.llm_call import LlmCall

MAX_QUEUE_SIZE = 1000
MAX_BATCH_SIZE = 20
FLUSH_INTERVAL_SECONDS = 5.0
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 1.0


@dataclass
class LlmCallRecord:
    purpose: LlmCallPurposeEnum
    model: str
    input_tokens: int
    output_tokens: int | None
    cost_usd: float | None
    latency_ms: int
    status: LlmCallStatusEnum
    trace_id: str | None = None


class LLMCallBatcher:
    def __init__(
        self,
        max_batch_size: int = MAX_BATCH_SIZE,
        flush_interval_seconds: float = FLUSH_INTERVAL_SECONDS,
        max_retries: int = MAX_RETRIES,
        max_queue_size: int = MAX_QUEUE_SIZE,
    ) -> None:
        self._max_batch_size = max_batch_size
        self._flush_interval_seconds = flush_interval_seconds
        self._max_retries = max_retries
        self._queue: asyncio.Queue[LlmCallRecord] = asyncio.Queue(maxsize=max_queue_size)
        self._task: asyncio.Task[None] | None = None

    def enqueue(self, record: LlmCallRecord) -> None:
        try:
            self._queue.put_nowait(record)
        except asyncio.QueueFull:
            try:
                dropped = self._queue.get_nowait()
                logfire.warning(
                    "LLM call log queue full, dropping oldest record for {model}",
                    model=dropped.model,
                )
                self._queue.put_nowait(record)
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                pass

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._drain()

    async def _run(self) -> None:
        buffer: list[LlmCallRecord] = []
        try:
            while True:
                try:
                    record = await asyncio.wait_for(
                        self._queue.get(), timeout=self._flush_interval_seconds
                    )
                    buffer.append(record)
                    if len(buffer) >= self._max_batch_size:
                        await self._flush(buffer)
                        buffer = []
                except TimeoutError:
                    if buffer:
                        await self._flush(buffer)
                        buffer = []
        except asyncio.CancelledError:
            if buffer:
                await self._flush(buffer)
            raise

    async def _drain(self) -> None:
        buffer: list[LlmCallRecord] = []
        while not self._queue.empty():
            buffer.append(self._queue.get_nowait())
        if buffer:
            await self._flush(buffer)

    async def _flush(self, batch: list[LlmCallRecord]) -> None:
        for attempt in range(self._max_retries):
            try:
                async with async_session_factory() as session:
                    session.add_all(
                        [
                            LlmCall(
                                id=uuid.uuid4(),
                                purpose=record.purpose,
                                model=record.model,
                                input_tokens=record.input_tokens,
                                output_tokens=record.output_tokens,
                                cost_usd=record.cost_usd,
                                latency_ms=record.latency_ms,
                                status=record.status,
                                trace_id=record.trace_id,
                            )
                            for record in batch
                        ]
                    )
                    await session.commit()
                return
            except Exception:
                logfire.exception(
                    "Failed to flush {count} LLM call records (attempt {attempt}/{max_retries})",
                    count=len(batch),
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                )
                await asyncio.sleep(BACKOFF_BASE_SECONDS * (2**attempt))
        logfire.warning(
            "Giving up on flushing {count} LLM call records after {max_retries} attempts",
            count=len(batch),
            max_retries=self._max_retries,
        )


llm_call_batcher = LLMCallBatcher()


def log_llm_call(
    purpose: LlmCallPurposeEnum,
    model: str,
    input_tokens: int,
    output_tokens: int | None,
    latency_ms: int,
    status: LlmCallStatusEnum,
    trace_id: str | None = None,
) -> None:
    cost_usd = (
        calculate_cost_usd(model, input_tokens, output_tokens or 0)
        if status == LlmCallStatusEnum.SUCCESS
        else None
    )
    llm_call_batcher.enqueue(
        LlmCallRecord(
            purpose=purpose,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            status=status,
            trace_id=trace_id,
        )
    )
