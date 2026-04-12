## ADDED Requirements

### Requirement: README.md
The addon SHALL include a `README.md` at `addons/newsassistant/README.md` documenting: module purpose and overview, installation prerequisites (queue_job, server config), configuration steps (API key, docker-compose, odoo.conf), usage instructions (kanban workflow, source management), and technical details (scraping pipeline, AI integration, queue job architecture).

#### Scenario: README covers installation
- **WHEN** a developer reads the README
- **THEN** they SHALL find step-by-step instructions for installing the module including all prerequisites

#### Scenario: README covers configuration
- **WHEN** an administrator reads the README
- **THEN** they SHALL find instructions for setting the Infomaniak API key, configuring odoo.conf, and updating docker-compose.yml

### Requirement: agents.md with definition of done
The addon SHALL include an `agents.md` at `addons/newsassistant/agents.md` documenting: the definition of done for the project, coding standards and conventions, testing requirements, and quality criteria for contributions.

#### Scenario: Definition of done is clear
- **WHEN** a developer reads agents.md
- **THEN** they SHALL find a clear checklist defining when a task or feature is considered complete

#### Scenario: Testing requirements documented
- **WHEN** a developer reads agents.md
- **THEN** they SHALL find requirements for unit test coverage, test patterns (trap_jobs, mocking), and how to run tests

### Requirement: Unit test suite
The addon SHALL include a comprehensive test suite under `addons/newsassistant/tests/` covering: model CRUD operations, HTML pre-cleaning logic, URL normalization and deduplication, AI API integration (with mocked HTTP responses), Stage 1 listing discovery (with mocked HTTP and AI), Stage 2 article extraction (with mocked HTTP and AI), cron job fan-out logic, kanban stage workflow, error handling and retry behavior. Tests SHALL run within Odoo's standard test framework using `odoo.tests.common.TransactionCase` or `HttpCase`. Queue job tests SHALL use the `trap_jobs()` context manager from `queue_job.tests.common`.

#### Scenario: Run test suite
- **WHEN** a developer runs `odoo -d newsassistant --test-tags newsassistant --stop-after-init`
- **THEN** all tests SHALL pass

#### Scenario: AI calls are mocked in tests
- **WHEN** tests exercise the scraping pipeline
- **THEN** no real HTTP requests SHALL be made to external websites or the Infomaniak API
- **THEN** tests SHALL use `unittest.mock.patch` to mock HTTP and AI responses

#### Scenario: Queue jobs tested with trap_jobs
- **WHEN** tests verify job creation
- **THEN** tests SHALL use `trap_jobs()` to assert correct jobs are enqueued without executing them
