"""havln_tools: pure-Python utilities for RoboWorld 2026 Track 2 (HA-VLN 2.0).

No Habitat dependency. Mirrors the official scoring formulas and the submission
contract from https://github.com/roboworld2026/track2 so that every agent in the
team scores, validates and packages submissions identically.
"""
from .score import (  # noqa: F401
    EpisodeResult,
    SplitMetrics,
    HUMAN_INFLUENCED,
    SPLIT_SIZES,
    aggregate,
    composite_score,
    episode_metrics,
    navigation_term,
    social_term,
)
from .contract import (  # noqa: F401
    ACTIONS,
    MAX_ACTIONS,
    ContractError,
    check_rows,
    load_prediction_file,
    validate_submission_zip,
    write_submission,
)
from .grouping import group_by_path  # noqa: F401
