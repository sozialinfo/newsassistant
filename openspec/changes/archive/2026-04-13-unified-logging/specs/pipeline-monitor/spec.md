## REMOVED Requirements

### Requirement: Pipeline Monitor menu item

**Reason**: Pipeline Monitor is being removed entirely. Its functionality is replaced by the new "Logs" and "Running Jobs" admin menus which provide more actionable operational data.

**Migration**: Use the "Logs" menu for viewing operation history with filtering. Use "Running Jobs" menu to see currently executing jobs.

### Requirement: Pipeline Monitor dashboard

**Reason**: The dashboard provided only aggregate counts without actionable detail. The new Logs view provides filterable, navigable log entries with full context.

**Migration**: Use the Logs view with filters (e.g., filter by level="error") to find problem areas. Use group-by to get category breakdowns.

### Requirement: Sources with errors stat button

**Reason**: Replaced by filtering in the Logs view and the existing source list which already shows error state.

**Migration**: Filter Sources list by `state='error'` or filter Logs by `level='error'` and group by source.

### Requirement: Articles pending stat button

**Reason**: Replaced by filtering in the Articles list which already supports state filtering.

**Migration**: Filter Articles list by `state='pending'`.

### Requirement: Articles with errors stat button

**Reason**: Replaced by filtering in the Articles list and Logs view.

**Migration**: Filter Articles list by `state='error'` or filter Logs by `level='error'` and `category='extraction'`.

### Requirement: Recent failures table

**Reason**: Replaced by the Logs view filtered to `level='error'` with date range filter. The Logs view provides richer detail including full error context and LLM interaction data.

**Migration**: Open Logs, filter by `level='error'`, optionally set date range to last 24 hours.

### Requirement: Dashboard refresh

**Reason**: No longer applicable as Pipeline Monitor is removed.

**Migration**: The Logs view uses standard Odoo list refresh behavior.
