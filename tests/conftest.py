import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Keep the attestation ledger out of the repo during tests.
os.environ.setdefault("GHOSTLINE_DB", str(Path(tempfile.gettempdir()) / "ghostline_test.db"))

# Tests must not read the developer's real .env: a real GEMINI_API_KEY / LLM_API_KEY there
# would send the extractor and pack generator to the live network (and real CALLE_API_KEY
# into runs). Force environment-only configuration for the whole test session.
from ghostline import config as _config

_config.Settings.model_config["env_file"] = None
_config.get_settings.cache_clear()

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
