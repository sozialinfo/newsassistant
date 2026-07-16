## ADDED Requirements

### Requirement: Snapshot hierarchy (parent/child)
The `news.snapshot` model SHALL support a parent/child hierarchy. A listing snapshot (containing multiple discoverable articles) SHALL have `is_listing=True`. Individual article snapshots created from a listing SHALL have `parent_id` pointing to the listing snapshot.

#### Scenario: Listing snapshot has is_listing=True
- **WHEN** a listing snapshot is created for a website listing page or newsletter email
- **THEN** the `is_listing` field SHALL be `True`

#### Scenario: Child snapshot links to parent
- **WHEN** a child snapshot is created from a listing snapshot
- **THEN** the `parent_id` SHALL point to the listing snapshot

#### Scenario: Listing snapshot has child snapshots
- **WHEN** a listing snapshot has 3 child snapshots
- **THEN** `child_ids` SHALL contain 3 records
- **THEN** `article_count` on the listing snapshot SHALL be 0 (articles are on child snapshots)

#### Scenario: Non-listing snapshot defaults
- **WHEN** a snapshot is created without specifying `is_listing`
- **THEN** `is_listing` SHALL be `False`
- **THEN** `parent_id` SHALL be `False`

### Requirement: Listing snapshots skip extraction, run discovery
When a listing snapshot (`is_listing=True`) is created, the system SHALL NOT enqueue `_extract_articles()`. Instead, it SHALL enqueue `_discover_articles()` to find child articles within the listing content.

#### Scenario: Listing snapshot enqueues discovery
- **WHEN** a listing snapshot is created
- **THEN** a queue job for `_discover_articles()` SHALL be enqueued
- **THEN** no queue job for `_extract_articles()` SHALL be enqueued for this snapshot

#### Scenario: Non-listing snapshot enqueues extraction (unchanged)
- **WHEN** a non-listing snapshot is created
- **THEN** a queue job for `_extract_articles()` SHALL be enqueued (existing behavior preserved)

### Requirement: _discover_articles() base method
The `news.snapshot` model SHALL define a `_discover_articles()` method that raises `NotImplementedError`. Each module that creates listing snapshots SHALL override this method to implement its own discovery logic.

#### Scenario: Base _discover_articles raises NotImplementedError
- **WHEN** `_discover_articles()` is called on a base `news.snapshot` record
- **THEN** a `NotImplementedError` SHALL be raised

#### Scenario: Child snapshots inherit parent's source
- **WHEN** a child snapshot is created via `_discover_articles()`
- **THEN** the child's `source_id` SHALL be the same as the parent listing snapshot's `source_id`