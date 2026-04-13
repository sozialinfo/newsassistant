## ADDED Requirements

### Requirement: German translation file exists
The module SHALL include a German translation file at `i18n/de.po` containing translations for all user-facing strings.

#### Scenario: German translations available
- **WHEN** the newsassistant module is installed and the user's language is set to German
- **THEN** all menu items, field labels, button labels, filter names, and messages display in German

### Requirement: French translation file exists
The module SHALL include a French translation file at `i18n/fr.po` containing translations for all user-facing strings.

#### Scenario: French translations available
- **WHEN** the newsassistant module is installed and the user's language is set to French
- **THEN** all menu items, field labels, button labels, filter names, and messages display in French

### Requirement: Consistent terminology
All translations SHALL use the established terminology defined in `agents.md`.

#### Scenario: Article terminology in German
- **WHEN** displaying the "News Article" model name in German
- **THEN** it displays as "Artikel" (not "Nachrichtenartikel" or "Beitrag")

#### Scenario: Stage terminology in German
- **WHEN** displaying the "Stage" field label in German
- **THEN** it displays as "Status" (not "Stufe" or "Phase")

#### Scenario: Article terminology in French
- **WHEN** displaying the "News Article" model name in French
- **THEN** it displays as "Article" (not "Article d'actualité")

### Requirement: Complete coverage
The translation files SHALL include translations for all msgid entries that appear in the exported POT template.

#### Scenario: No empty translations
- **WHEN** reviewing the de.po or fr.po file
- **THEN** every msgid has a non-empty msgstr (except the header block)

### Requirement: Valid PO format
The translation files SHALL be valid gettext PO format files that Odoo can import without errors.

#### Scenario: Successful import
- **WHEN** importing de.po or fr.po into Odoo using `--i18n-import`
- **THEN** the import completes without errors
