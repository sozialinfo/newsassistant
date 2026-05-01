## MODIFIED Requirements

### Requirement: Article stage model
The system SHALL provide a `news.article.stage` model with fields: `name` (Char, required, translatable), `sequence` (Integer), and `fold` (Boolean, default False). Default stages SHALL be created via data XML: New (sequence 10, not folded), Shortlist (sequence 20, not folded), Published (sequence 30, folded), Discarded (sequence 40, folded).

#### Scenario: Default stages exist after install
- **WHEN** the module is installed
- **THEN** four stages SHALL exist: New, Shortlist, Published, Discarded
- **THEN** stages SHALL be ordered by sequence

#### Scenario: Published and Discarded are folded
- **WHEN** the kanban view is rendered
- **THEN** the Published and Discarded columns SHALL be folded by default

#### Scenario: New and Shortlist are not folded
- **WHEN** the kanban view is rendered
- **THEN** the New and Shortlist columns SHALL be visible (not folded)
