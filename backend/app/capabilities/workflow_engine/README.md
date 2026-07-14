# workflow_engine Capability

**Domain:** infrastructure | **Layer:** application | **Version:** 1.0.0

## Description

Generic workflow engine: approvals, states, transitions, business rules, timers, escalations, notifications, audit trail

## Dependencies

- notification_service
- audit_logging

## API

-
 
`
/
w
o
r
k
f
l
o
w
-
e
n
g
i
n
e
/
`
 
—
 
R
E
S
T
 
A
P
I

## Events

- `WorkflowCreated`
- `WorkflowTransitioned`
- `WorkflowCompleted`
- `WorkflowEscalated`
- `WorkflowCancelled`

## Commands

- `create_workflow`
- `transition`
- `escalate`
- `cancel_workflow`

## Queries

- `get_workflow`
- `list_workflows`
- `get_pending_tasks`

## Quality

- Quality Score: 0.0
- Security Score: 0.0
- Performance Score: 0.0
- Reuse Score: 1.0

## License

Proprietary - GULA Platform
