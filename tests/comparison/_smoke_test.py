"""Smoke test script for the comparison pipeline.
Generates synthetic data since ANTHROPIC_API_KEY is not set in this environment.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import json
from typing import Any
from datetime import datetime, timezone

from tests.comparison import metrics as metrics_mod
from tests.comparison import report as report_mod

# --- Synthetic data based on reasonable expectation for this task ---
single_metrics: dict[str, Any] = {
    'input_tokens': 850,
    'output_tokens': 2100,
    'total_tokens': 2950,
    'duration_seconds': 18.4,
    'task_completed': True,
    'errors': [],
    'api_calls': 1,
    'api_cost_estimated': 0.0340,
    'code_correctness': 3,
    'code_completeness': 4,
    'code_quality': 3,
    'documentation_quality': 3,
    'overall_score': 3.25,
    'model': 'claude-sonnet-4-20250514',
    'validation_passed': True,
    'validation_messages': [],
}

multi_metrics: dict[str, Any] = {
    'input_tokens': 6850,
    'output_tokens': 2900,
    'total_tokens': 9750,
    'duration_seconds': 45.7,
    'task_completed': True,
    'errors': [],
    'api_calls': 2,
    'api_cost_estimated': 0.0740,
    'code_correctness': 4,
    'code_completeness': 5,
    'code_quality': 4,
    'documentation_quality': 4,
    'overall_score': 4.25,
    'model': 'claude-sonnet-4-20250514',
    'validation_passed': True,
    'validation_messages': [],
}

comparison = metrics_mod.compute_comparison(single_metrics, multi_metrics)
report_mod.print_comparison_table(comparison)
exported_path = report_mod.export_json(comparison, 'comparison_result.json')
print(f'\nResults written to: {exported_path}')
