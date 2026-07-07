# MVP Scope: Multi-Agent vs Single-Agent Comparison

## 1. Project Context and Problem Statement

This project investigates whether dividing a software development task among multiple specialized AI agents (multi-agent mode) performs better than assigning the same task to a single all-in-one AI agent (single-agent mode). The target environment is this project (AI Embedded Systems Company) which already defines 18 agent roles and a LangGraph-based orchestrator.

**Core Question**: For a given representative embedded systems development task, which mode delivers better results per unit of compute cost?

| Dimension | Multi-Agent | Single-Agent |
|-----------|-------------|--------------|
| Team composition | Specialized roles (e.g., firmware engineer + hardware engineer + reviewer) | One agent does everything |
| Workflow | Pipeline with handoffs between roles | Monolithic execution |
| Token cost | Higher overhead (role instructions, context handoff) | Lower overhead, one continuous context |
| Quality | Potential for deeper specialization | Potential for inconsistency |

---

## 2. MVP Definition -- Smallest Useful Experiment

The MVP answers one concrete research question with a single controlled experiment:

> **"For a given embedded firmware task, does multi-agent collaboration produce higher-quality output than a single agent, and at what token cost ratio?"**

### MVP Feature List

1. **Comparison Runner** -- A Python script that:
   - Accepts a task specification (plain text)
   - Invokes both modes on that task
   - Collects the same metrics from both modes
   - Outputs a structured comparison report

2. **Single-Agent Mode** -- One agent call (claude-api) that receives the full task spec and delivers the complete deliverable.

3. **Multi-Agent Mode** -- A fixed 2-agent pipeline:
   - Agent 1: `backend-developer` (implements the solution)
   - Agent 2: `code-reviewer` (reviews and provides feedback)
   - A Python harness orchestrates handoff, no LangGraph dependency needed.

4. **Metrics Collector** -- Record per-run data including token counts, timing, error tracking.

5. **Report Generator** -- Produce a formatted comparison report (console output + CSV/JSON export).

### Explicitly Out of Scope (Non-MVP)

- More than 2 agents in the multi-agent mode
- Integration with the project's FastAPI or MCP infrastructure
- Production deployment or dashboard integration
- Statistical significance testing (MVP is a single experiment run, repeatable)
- Multiple task types (MVP uses one representative embedded task)

---

## 3. Metrics Definition

### Primary Metrics

| Metric | Definition | Unit | Collection Method |
|--------|-----------|------|-------------------|
| Token Consumption (Input) | Total prompt tokens sent to the LLM | tokens | Parsed from API response `usage.input_tokens` |
| Token Consumption (Output) | Total completion tokens generated | tokens | Parsed from API response `usage.output_tokens` |
| Token Consumption (Total) | Input + Output sum | tokens | Computed from the two above |
| Wall Clock Time | Real elapsed time from start to finish | seconds | `time.monotonic()` before/after |
| Task Completion | Did the agent produce the required deliverable? | boolean | Manual check + automated validation |
| Error Occurrence | Did any API call fail or produce empty result? | boolean | Exception tracking in harness |

### Qualitative Metrics (Structured Human Review)

| Metric | Scale | Assessment Criteria |
|--------|-------|-------------------|
| Code Correctness | 1-5 | Compilation errors, logic bugs |
| Code Completeness | 1-5 | All requested features present |
| Code Quality | 1-5 | Naming, structure, error handling |
| Documentation Quality | 1-5 | Comments, README quality |
| Overall Score | 1-5 | Holistic assessment |

### Derived Metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| Tokens per Quality Point | Total tokens / Overall Score | Cost-efficiency ratio |
| Quality per Dollar | Overall Score / Estimated API cost ($) | Value comparison |
| Error Rate | Failed API calls / Total API calls | Reliability indicator |

---

## 4. Test Scenario -- Representative Embedded Firmware Task

### The Task: "M5Stack Core S3 Temperature Logger"

A realistic embedded firmware task that exercises multiple skill areas:

**Specification**:
```
Write an Arduino-compatible firmware for the M5Stack Core S3 that:
1. Reads temperature from the internal BMI270 IMU (acceleration only -- simulated temperature)
2. Displays the temperature on the TFT screen (ILI9342C, 320x240)
3. Logs data to the microSD card every 10 seconds
4. Uses the button (GPIO 41) to toggle between Celsius/Fahrenheit
5. Handles errors gracefully (SD card missing, sensor init failure)
6. Prints debug info over Serial at 115200 baud

Deliverables:
- One .ino file with the full firmware
- Brief README with wiring/pinout and build instructions
```

**Why this task**: It touches sensor I2C communication, TFT display rendering, SD card filesystem operations, GPIO button handling, error handling, and serial debug -- a realistic embedded firmware scope that would benefit from specialization.

### Multi-Agent Split Plan (for the MVP pipeline)

| Step | Agent Role | Responsible For |
|------|-----------|----------------|
| 1 | `embedded-firmware-engineer` | Core implementation (all firmware code) |
| 2 | `code-reviewer` | Review code for correctness, completeness, error handling, edge cases |

### Single-Agent Mode

| Step | Agent Role | Responsible For |
|------|-----------|----------------|
| 1 | `embedded-firmware-engineer` | Everything (implementation + self-review, prompted to do both) |

---

## 5. Data Collection and Visualization

### Collected Data Schema (stored as JSON)

```json
{
  "run_id": "comparison-20260708-001",
  "timestamp": "2026-07-08T10:00:00Z",
  "task": "temperature-logger",
  "mode": "single-agent",
  "mode": {
    "name": "multi-agent",
    "agents": ["embedded-firmware-engineer", "code-reviewer"]
  },
  "metrics": {
    "input_tokens": 4500,
    "output_tokens": 2800,
    "total_tokens": 7300,
    "duration_seconds": 45.2,
    "task_completed": true,
    "errors": [],
    "api_calls": 2,
    "api_cost_estimated": 0.15
  },
  "quality": {
    "code_correctness": 4,
    "code_completeness": 5,
    "code_quality": 4,
    "documentation_quality": 3,
    "overall_score": 4,
    "reviewer_notes": "All functions present, error paths handled."
  }
}
```

### Visualization Output (MVP)

A console table and a JSON export. Full visualization (charts, dashboards) is post-MVP.

**Console Output Format**:
```
=======================================================
 COMPARISON RESULT: Temperature Logger Task
=======================================================
Metric                     Single-Agent   Multi-Agent   Delta
--------------------------------------------------------------
Input tokens               4,500          6,200         +38%
Output tokens              2,800          3,100         +11%
Total tokens               7,300          9,300         +27%
Duration (s)               45.2           72.8          +61%
Task completed             Yes            Yes            --
API calls                  1              2             +100%
Est. cost ($)              $0.15          $0.19         +27%
Code Correctness (1-5)     3              4             +1
Code Completeness (1-5)    4              5             +1
Code Quality (1-5)         3              4             +1
Doc Quality (1-5)          3              3             --
Overall Score (1-5)        3.25           4.0           +23%
Tokens per Quality Point   2,246          2,325         +4%
=======================================================
Conclusion: Multi-agent scored 23% higher quality at 27% more tokens.
```

---

## 6. Test Harness Architecture

### Files to Create

```
tests/comparison/
├── __init__.py
├── runner.py              # Main test harness
├── modes/
│   ├── __init__.py
│   ├── single.py          # Single-agent execution
│   └── multi.py           # Multi-agent (2-agent pipeline)
├── metrics.py             # Data collection + storage
├── report.py              # Report formatting + export
├── tasks/
│   ├── __init__.py
│   └── temperature_logger.py   # Task specification + validation
└── run_comparison.py      # Entry point: python run_comparison.py
```

### Architecture Overview

```
                  ┌─────────────────────────────────────┐
                  │         run_comparison.py            │
                  │  (CLI entry point)                   │
                  └────────────┬─────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │     runner.py        │
                    │  - loads task spec   │
                    │  - calls both modes  │
                    │  - collects metrics  │
                    │  - generates report  │
                    └────┬──────────┬──────┘
                         │          │
              ┌──────────┘          └──────────┐
              │                                 │
    ┌─────────┴──────────┐        ┌─────────────┴─────────┐
    │   modes/single.py   │        │    modes/multi.py      │
    │  - calls Claude API │        │  - Agent 1: firmware   │
    │  - one-shot prompt  │        │    - Agent 2: review   │
    │  - returns result   │        │  - pipes context       │
    └─────────┬───────────┘        │  - returns result      │
              │                    └─────────────┬───────────┘
              │                                 │
              └──────────┬──────────────────────┘
                         │
                ┌────────┴────────┐
                │   metrics.py    │
                │  - parse API    │
                │    responses    │
                │  - extract       │
                │    token counts  │
                │  - store to JSON │
                └────────┬────────┘
                         │
                ┌────────┴────────┐
                │   report.py     │
                │  - console      │
                │    comparison   │
                │  - JSON export  │
                └─────────────────┘
```

### Key Design Decisions

1. **Use Anthropic SDK directly** (not FastAPI or MCP) to minimize infrastructure dependencies -- pure Python script, runnable with `uv run python tests/comparison/run_comparison.py`
2. **Hardcoded API key** from environment variable `ANTHROPIC_API_KEY`
3. **Prompt templates** defined as Python f-strings with task description injection
4. **Model**: `claude-sonnet-4-20250514` for both modes (same model to isolate the mode variable)
5. **Multi-agent handoff**: Agent 2 receives Agent 1's full output in its context, not via separate tool calls

### Claude API Endpoint

- **API**: Messages API (POST https://api.anthropic.com/v1/messages)
- **SDK**: `anthropic` Python SDK (pip installable, `anthropic>=0.49`)
- **Token counting**: Use `usage.input_tokens` and `usage.output_tokens` from the API response
- **Streaming**: Off for MVP (simple blocking calls)

---

## 7. Deliverables

### Required Deliverables

| # | Deliverable | Description | Acceptance Criteria |
|---|-----------|-------------|---------------------|
| 1 | `tests/comparison/runner.py` | Main harness: accepts task spec, executes both modes, orchestrates pipeline | `python -c "from tests.comparison.runner import run_comparison; run_comparison()"` executes without error |
| 2 | `tests/comparison/modes/single.py` | Single-agent mode implementation | Makes one API call; returns dict with `{raw_response, metrics}` |
| 3 | `tests/comparison/modes/multi.py` | Multi-agent mode (2-agent pipeline) | Makes two API calls in sequence; agent 2 receives agent 1 output; returns same dict shape as single.py |
| 4 | `tests/comparison/metrics.py` | Metric collection from API responses | Parses token counts, timing, errors from Anthropic SDK response |
| 5 | `tests/comparison/report.py` | Comparison report generation | Outputs a formatted table to stdout AND writes `comparison_result.json` |
| 6 | `tests/comparison/tasks/temperature_logger.py` | Task specification and validator | `validate()` checks deliverables exist and have expected structure |
| 7 | `tests/comparison/run_comparison.py` | Entry point CLI script | `uv run python tests/comparison/run_comparison.py` produces a complete comparison output |
| 8 | `tests/comparison/__init__.py` | Package init | Empty or minimal |

### Non-Deliverable (Post-MVP)

- Web dashboard / chart visualization
- Integration with the project's database (storage/models.py)
- Statistical analysis across multiple runs
- Automated report email or notification
- MCP tool wrappers
- CI/CD pipeline integration

---

## 8. Acceptance Criteria

The MVP is complete when:

1. **Execution**: `uv run python tests/comparison/run_comparison.py` runs end-to-end without errors
2. **API Connectivity**: Both modes successfully call the Claude API and return valid responses
3. **Metrics Collected**: Both runs produce valid token counts, timing, and completion status
4. **Report Output**: A formatted comparison table is printed to stdout
5. **Data Export**: A `comparison_result.json` file is written with full structured data
6. **Repeatability**: Running the script a second time produces a valid (though possibly different) comparison
7. **Error Handling**: If the API key is missing, the script produces a clear error message and exits gracefully
8. **No Database Required**: All state is ephemeral (in-memory metrics, JSON file output)
9. **Task Validation**: The temperature_logger module has a `validate(result: dict) -> bool` function that can verify the output structure

---

## 9. Implementation Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| API key not configured | Medium | High | Clear error message at startup, documented env var setup |
| API rate limits | Low | Medium | 3-second delay between calls, documented in runner |
| Token counts from SDK not available | Low | Medium | Fall back to estimating via tiktoken |
| Multi-agent handoff context window exceeded | Medium | Medium | Prompt agent 1 to be concise; cap response at 4000 tokens |
| Output quality varies between runs (non-deterministic) | High | Medium | Run comparison 3x per mode, report average; or accept single-run as indicative |

---

## 10. Implementation Plan (Steps)

### Step 1: Create Package Structure
```bash
mkdir -p tests/comparison/modes tests/comparison/tasks
touch tests/comparison/__init__.py
touch tests/comparison/modes/__init__.py
touch tests/comparison/tasks/__init__.py
```

### Step 2: Implement `tests/comparison/tasks/temperature_logger.py`
- Define `TASK_SPEC` string (the firmware task description)
- Define `EXPECTED_DELIVERABLES` list
- Implement `validate(result: dict) -> tuple[bool, list[str]]`

### Step 3: Implement `tests/comparison/metrics.py`
- `extract_metrics(api_response: dict) -> dict`
- `compute_comparison(single_metrics: dict, multi_metrics: dict) -> dict`

### Step 4: Implement `tests/comparison/modes/single.py`
- Create prompt template
- Call Claude API with Anthropic SDK
- Return {response, metrics}

### Step 5: Implement `tests/comparison/modes/multi.py`
- Create two prompt templates (implementation, review)
- Call agent 1, pipe output to agent 2's context
- Call agent 2
- Return {agent1_response, agent2_response, metrics}

### Step 6: Implement `tests/comparison/report.py`
- Pretty-print ASCII table
- JSON export

### Step 7: Implement `tests/comparison/runner.py`
- Orchestrate the full flow
- Error handling for missing API key, API failures

### Step 8: Implement `tests/comparison/run_comparison.py`
- CLI entry point with argparse (optional: task name, output path)

---

## Appendix A: Prompt Templates for Each Mode

### Single-Agent Prompt
```
You are an embedded firmware engineer. Implement the following complete firmware
for the M5Stack Core S3. Include all edge case handling, error paths, and comments.

Task:
{task_spec}

Deliver a single .ino file and a brief README with build instructions.
```

### Multi-Agent Step 1 (Firmware Engineer)
```
You are an embedded firmware engineer specialized in M5Stack Core S3 (ESP32-S3).
Implement the following firmware:

Task:
{task_spec}

Deliver a single .ino file with complete implementation.
Include all error handling, initialization checks, and comments.
```

### Multi-Agent Step 2 (Code Reviewer)
```
You are a senior code reviewer for embedded systems. Review the following firmware
implementation for the M5Stack Core S3 temperature logger.

TASK SPECIFICATION:
{task_spec}

IMPLEMENTATION TO REVIEW:
{agent1_output}

Your review should check:
1. Code correctness -- does it compile and run?
2. Completeness -- are all 6 requirements implemented?
3. Error handling -- SD card, sensor, edge cases?
4. Code quality -- naming, structure, comments?
5. Safety -- buffer overflows, race conditions, resource leaks?

Provide:
- A score (1-5) for each category listed above
- Specific improvement suggestions (minimum 2 if score < 4)
- A final revised .ino file incorporating your suggested fixes
- Brief README with build instructions
```

---

## Appendix B: Example Metrics Flow Data

```
run_comparison()
  ├── task = load_task("temperature_logger")
  ├── single_metrics = run_single_mode(task)
  │   ├── api_call(anthropic, prompt_single, task.spec)
  │   ├── token_count = response.usage.input_tokens + response.usage.output_tokens
  │   ├── duration = time.monotonic() - start
  │   └── errors = [] (or ["timeout"] etc.)
  │
  ├── multi_metrics = run_multi_mode(task)
  │   ├── api_call(agent1, prompt_implement, task.spec)
  │   │   ├── token_count_1
  │   │   └── duration_1
  │   ├── api_call(agent2, prompt_review, task.spec + agent1.output)
  │   │   ├── token_count_2
  │   │   └── duration_2
  │   ├── total_tokens = token_count_1 + token_count_2
  │   └── total_duration = duration_1 + duration_2 + 3s_delay
  │
  ├── comparison = compute_comparison(single_metrics, multi_metrics)
  ├── print_report(comparison)
  └── export_json(comparison, "comparison_result.json")
```
