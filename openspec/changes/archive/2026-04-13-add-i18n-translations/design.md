## Context

The newsassistant Odoo module has ~100 translatable strings spread across Python models, XML views, and data files. Odoo's standard i18n system uses gettext-format .po files stored in `i18n/` directories. The POT (template) file can be exported from a running Odoo instance, then translated into target languages.

Target languages: German (de) and French (fr) - standard variants, not Swiss-specific.

Terminology has been established in `agents.md`:
| English | German | French |
|---------|--------|--------|
| Article | Artikel | Article |
| Stage | Status | Étape |
| Source | Quelle | Source |
| Relevant | Relevant | Pertinent |

## Goals / Non-Goals

**Goals:**
- Complete German and French translations for all user-facing strings
- Follow standard Odoo i18n conventions (PO file format, directory structure)
- Consistent terminology across all translations

**Non-Goals:**
- Swiss German or Swiss French variants (use standard DE/FR)
- Runtime language detection or auto-switching
- Translation of technical/debug messages in logs
- Translation management UI or workflow

## Decisions

### 1. Use LLM for translation (vs. manual or translation service)

**Decision**: Generate translations using LLM with established terminology glossary.

**Rationale**: 
- ~100 strings is manageable scope
- Domain terminology is specific (news/media context)
- Glossary ensures consistency
- Faster iteration than external translation service

**Alternative considered**: Professional translation service - overkill for this scope, slower turnaround.

### 2. Standard PO format (vs. CSV)

**Decision**: Use .po file format, not Odoo's CSV alternative.

**Rationale**:
- Industry standard, tooling support (Poedit, etc.)
- Better diff/merge in version control
- Matches Odoo core module conventions

### 3. Single .po file per language (vs. split by model)

**Decision**: One `de.po` and one `fr.po` covering all module strings.

**Rationale**:
- Standard Odoo convention
- Module is small enough that splitting adds no value
- Simpler maintenance

### 4. No manifest change required

**Decision**: Odoo auto-discovers `i18n/*.po` files - no `__manifest__.py` change needed.

**Rationale**: Odoo's module loader automatically scans `i18n/` directory for .po files matching installed languages.

## Risks / Trade-offs

**[Risk] Translation drift as code changes** → Documented update procedure in `agents.md`. Re-export POT and merge new strings when needed.

**[Risk] Inconsistent terminology** → Established glossary in `agents.md`. All translations must follow it.

**[Risk] LLM mistranslation of technical terms** → Review translations before commit. Technical terms (Scrape, Queue Job) kept in context.

**[Trade-off] No professional review** → Acceptable for internal tool. Can be refined based on user feedback.
