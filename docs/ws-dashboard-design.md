# Dashboard Agent Live-Tracking — WebSocket Design

## Overview
Add real-time agent status updates to the React dashboard via a WebSocket endpoint. Existing REST endpoints provide the initial data; WebSocket pushes subsequent state changes.

## Proposed Architecture

```
FastAPI WebSocket /api/ws/agent-status
     │
     ├── Broadcasts on task/timer state changes
     │     • Task status transitions (todo → in_progress → review → done)
     │     • Token burn rate updates (via /api/tasks/{id}/tokens)
     │     • Cycle timeline events (via /api/system/event)
     │
     └── Message format (JSON):
         {
           "type": "agent:status" | "task:update" | "tokens:burn" | "cycle:event",
           "payload": { ... },
           "ts": "2026-07-10T12:00:00Z"
         }
```

## No Schema Changes Required
The existing database models already contain all needed fields:
- `TaskModel` — `started_at`, `completed_at`, `assigned_agent`, `tokens_used`, `status`
- `EventLogModel` — `event_type`, `source`, `payload`, `created_at`

## Implementation Plan

### Phase 1: FastAPI WebSocket endpoint (1 session)
- Add `@app.websocket("/api/ws/agent-status")` to `system.py`
- Maintain a set of active connections
- On task/token/event state changes, broadcast to all connected clients

### Phase 2: React hook + Dashboard component (1 session)
- `useWebSocket()` hook in `dashboard/src/hooks/`
- Connect on Dashboard mount, reconnect on disconnect
- Dispatch events to agent status cards, token chart, timeline

### Phase 3: Auto-refresh + animations (1 session)
- Task queue with completion animations
- Cycle timeline visualization (agent handoffs, review loops)
- Idle/active status indicator

## Message Types

| Type | Payload | Trigger |
|------|---------|---------|
| `task:update` | `{id, title, status, agent, project_id}` | PATCH task status |
| `tokens:burn` | `{task_id, agent, tokens, project_id}` | POST task tokens |
| `cycle:event` | `{event_type, source, payload}` | POST system event |
| `agent:status` | `{agent, status, task_id, elapsed_seconds}` | Computed from task state |

## API Contract

```typescript
// Client sends (optional subscription filter):
interface Subscribe {
  type: "subscribe";
  channels: string[]; // ["tasks", "tokens", "events"]
}

// Server pushes:
interface AgentStatusEvent {
  type: "agent:status";
  payload: {
    agent: string;
    status: "idle" | "working" | "reviewing";
    task_id?: string;
    elapsed_seconds: number;
  };
  ts: string;
}

interface TaskUpdateEvent {
  type: "task:update";
  payload: {
    id: string;
    title: string;
    status: string;
    assigned_agent?: string;
    project_id: string;
  };
  ts: string;
}
```
