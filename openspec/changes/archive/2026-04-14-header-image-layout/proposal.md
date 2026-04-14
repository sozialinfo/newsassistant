## Why

The header image display in article views has layout issues:
1. In kanban view, the header image is too large (full-width) instead of a small square in the corner
2. In form view, the header image is placed awkwardly in the right column alongside other fields with a label

These issues make the UI inconsistent with standard Odoo patterns (like `res.partner` kanban cards) and waste screen space.

## What Changes

- **Kanban view**: Change header image from full-width display to a small square in the top-right corner of the card, following the `res.partner` kanban pattern using Odoo 18's flex-row card layout
- **Form view**: Reorganize the header group to place all fields in the left column, reserving the right column exclusively for the header image without a label (empty if no image)

## Capabilities

### New Capabilities

(none - this is a view layout change only)

### Modified Capabilities

(none - no spec-level behavior changes, only visual layout)

## Impact

- `newsassistant/views/news_article_views.xml`: Kanban view template and form view group layout changes
- No model changes
- No API changes
- No new dependencies
