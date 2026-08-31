import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from ghostline.claim_pack import load_pack
from ghostline.models import (
    CallOutcome,
    Record,
    Speaker,
    Transcript,
    TranscriptTurn,
)


@pytest.fixture
def healthcare():
    return load_pack("healthcare")


@pytest.fixture
def record():
    return Record(
        record_id="r1",
        name="Northline Family Clinic",
        phone="+12025550110",
        address="1420 Oak St, Suite 300",
        region="US",
        claims={"accepts_plan": True},
    )


def convo(*user_lines: str, bot: str = "Do you accept the Northline Health plan?") -> Transcript:
    turns = [TranscriptTurn(speaker=Speaker.BOT, text=bot)]
    for line in user_lines:
        turns.append(TranscriptTurn(speaker=Speaker.USER, text=line))
    return Transcript(call_id="c1", outcome=CallOutcome.CONVERSATION, turns=turns)
