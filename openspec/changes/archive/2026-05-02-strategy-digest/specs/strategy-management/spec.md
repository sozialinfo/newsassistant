## ADDED Requirements

### Requirement: Strategy model
The system SHALL provide a `strategy.strategy` model with fields: `name` (Char, required), `date_from` (Date, optional), `date_to` (Date, optional), `document_ids` (Many2many → `ir.attachment`, domain: PDF only), `label_ids` (Many2many → `strategy.label`), `prompt` (Text, readonly, AI-generated), `description` (Text, optional, user-written summary). A strategy with no dates SHALL be treated as eternal (active for all time).

#### Scenario: Create a strategy with date range
- **WHEN** a user creates a strategy "Digital Transformation" with date_from 2026-01-01 and date_to 2026-12-31
- **THEN** the strategy SHALL be active only for articles dated within that range

#### Scenario: Strategy with no dates is always active
- **WHEN** a strategy has no date_from and no date_to
- **THEN** the strategy SHALL be considered active for all time periods

#### Scenario: Strategy with only date_from is active from that date onwards
- **WHEN** a strategy has date_from set but no date_to
- **THEN** the strategy SHALL be active from date_from onwards indefinitely

### Requirement: Strategy PDF document upload
The system SHALL allow users to upload multiple PDF documents to a strategy via the `document_ids` Many2many field. The documents are stored as `ir.attachment` records. The domain SHALL restrict uploads to PDF mime types.

#### Scenario: Upload PDF documents to strategy
- **WHEN** a user uploads two PDF files on a strategy form
- **THEN** both files SHALL be stored as `ir.attachment` records linked to the strategy
- **THEN** both SHALL appear in the `document_ids` widget on the form

#### Scenario: Non-PDF attachment is filtered
- **WHEN** the document upload widget is rendered
- **THEN** the domain `[('mimetype', 'like', 'pdf')]` SHALL restrict visible attachments to PDFs

### Requirement: Strategy prompt distillation
The system SHALL provide an action button "Distill Prompt" on the `strategy.strategy` form. When triggered, the system SHALL: extract text from all uploaded PDF documents using `pdfminer.six`, concatenate the extracted text with label names and the strategy description, call the AI (qwen3 via Infomaniak), and store the returned prompt in `strategy.prompt`. The prompt instructs which articles are relevant and how to label them.

#### Scenario: Distill prompt from PDFs and labels
- **WHEN** a user clicks "Distill Prompt" on a strategy with uploaded PDFs and assigned labels
- **THEN** the system SHALL extract text from each PDF
- **THEN** the system SHALL call the AI with the extracted text, label names, and description
- **THEN** the AI-generated prompt SHALL be saved to `strategy.prompt`
- **THEN** a success notification SHALL be shown to the user

#### Scenario: Distill with no PDFs uses description only
- **WHEN** a user clicks "Distill Prompt" on a strategy with no PDFs but a description text
- **THEN** the system SHALL call the AI with the description and label names only
- **THEN** the prompt SHALL be generated and saved

#### Scenario: Scanned PDF yields no text
- **WHEN** a PDF contains only scanned images (no extractable text)
- **THEN** the system SHALL log a warning and skip that document
- **THEN** distillation SHALL continue with remaining documents

#### Scenario: No content to distill from
- **WHEN** a user clicks "Distill Prompt" on a strategy with no PDFs and no description
- **THEN** the system SHALL raise a UserError informing the user that no content is available

### Requirement: Strategy list and form views
The system SHALL provide a list view and a form view for `strategy.strategy`. The form SHALL display all fields including the distilled prompt. The list view SHALL show name, date_from, date_to, and the count of labels. Strategies SHALL be accessible via the "Strategy Digest" menu.

#### Scenario: Navigate to strategies
- **WHEN** a user clicks "Strategy Digest" → "Strategies"
- **THEN** the list view of strategies SHALL be displayed

#### Scenario: Form shows all strategy fields
- **WHEN** a user opens a strategy form
- **THEN** all fields (name, dates, documents, labels, description, prompt) SHALL be visible
