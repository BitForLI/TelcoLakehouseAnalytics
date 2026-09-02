"""Optional Databricks Model Serving client for aggregate-only summaries."""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable


def build_grounded_prompt(evidence: dict[str, object]) -> str:
    return (
        "You are a telecommunications data analyst. Summarise the supplied aggregate metrics "
        "for a business stakeholder in at most five bullets. Every numeric statement must appear "
        "in the evidence. Do not infer causation, do not invent trends, and finish with one "
        "testable next action. Evidence:\n" + json.dumps(evidence, sort_keys=True)
    )


def request_databricks_summary(
    *,
    host: str,
    token: str,
    endpoint: str,
    evidence: dict[str, object],
    opener: Callable[..., object] = urllib.request.urlopen,
) -> str:
    """Call a Databricks serving endpoint without sending customer-level records."""

    url = f"{host.rstrip('/')}/serving-endpoints/{endpoint}/invocations"
    body = json.dumps(
        {
            "messages": [{"role": "user", "content": build_grounded_prompt(evidence)}],
            "temperature": 0.1,
            "max_tokens": 500,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with opener(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return str(payload["choices"][0]["message"]["content"])
