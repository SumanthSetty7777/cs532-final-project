from __future__ import annotations

from typing import List


class ModelRunner:
    """
    Simple batch inference runner.

    For the mid-project, this uses a dummy implementation so we can
    validate the full pipeline before plugging in a real model.
    """

    def __init__(self) -> None:
        # Later, load a real model here once at startup.
        pass

    def run_batch(self, texts: List[str]) -> List[str]:
        """
        Process a batch of inputs and return one output per input.
        """
        return [f"processed: {text}" for text in texts]
