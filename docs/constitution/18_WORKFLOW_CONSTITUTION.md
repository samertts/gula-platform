# GULA Workflow Constitution

## Workflow Philosophy

Clinical and laboratory workflows are the core value GULA delivers. Well-designed workflows reduce errors, improve efficiency, and ensure consistent care delivery. GULA supports both fixed workflows (regulatory requirement) and flexible workflows (clinical judgment).

## Workflow Design Principles

1. **Minimize cognitive load.** Each step should require only the information needed for that step. Present options, not blank forms.

2. **Default to the most common path.** Smart defaults, pre-populated values, and intelligent suggestions reduce keystrokes.

3. **Support exceptions.** Common workflows have standard paths. Exceptions (cancel order, reject sample, amend result) are first-class citizens, not afterthoughts.

4. **Undo is supported** where clinically safe. Destructive actions (delete result, void order) require confirmation and audit.

5. **Workflow state is persisted.** Users can leave a multi-step workflow and resume from where they stopped.

## Workflow Types

| Type | Description | Example |
|------|-------------|---------|
| **Clinical** | Patient care workflows | Order → Collect → Process → Result → Review → Act |
| **Laboratory** | Lab operations | Sample receipt → Accession → Analysis → Validation → Report |
| **Administrative** | Business operations | Staff onboarding → Role assignment → Facility provisioning |
| **Public Health** | Population health | Case detection → Investigation → Reporting → Intervention |
| **Compliance** | Regulatory | Incident report → Investigation → Corrective action → Closure |
| **Integration** | System-to-system | Order receive → Transform → Validate → Forward → Acknowledge |

## State Machines

7. **Complex workflows use a state machine** defined in `app/domain/`. States, transitions, guards, and side effects are explicit.

8. **State machines are testable in isolation.** Every state transition is tested.

9. **State machines emit events** on transitions for integration with other domains. See Article 16 (Event Constitution) for event schema and delivery guarantees.

## Workflow Engine

10. **GULA uses a lightweight workflow engine** for multi-step, multi-actor workflows.

11. **Workflow definitions** are configurable per tenant where regulation allows.

12. **Long-running workflows** support pause, resume, and timeout with escalation.

## Notifications

13. **Workflow transitions trigger notifications** to relevant actors. Users are notified of tasks assigned to them.

14. **Escalation paths** are defined for stalled workflows. If a lab result is not validated within 2 hours, the senior technician is notified. If still unvalidated after 4 hours, the lab director is notified.
