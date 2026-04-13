## Why

The News Assistant module currently has no translations - all UI labels, field names, and messages are in English only. Users working in German or French cannot use the application in their preferred language. Adding i18n support is a standard Odoo practice and improves accessibility for the Swiss social-sector audience (German and French are primary languages).

## What Changes

- Create `i18n/` directory with German (de.po) and French (fr.po) translation files
- Translate ~100 strings covering:
  - Menu items and window actions
  - Field labels and help text
  - Filter and group-by labels
  - Stage names and state values
  - Notification messages and error text
- Register translation files in `__manifest__.py`

## Capabilities

### New Capabilities

- `i18n-support`: German and French translations for all user-facing strings in the newsassistant module

### Modified Capabilities

None - this change adds translations without modifying existing behavior.

## Impact

- **Files added**: `addons/newsassistant/i18n/de.po`, `addons/newsassistant/i18n/fr.po`
- **Files modified**: `addons/newsassistant/__manifest__.py` (if i18n path registration needed)
- **Dependencies**: None - uses standard Odoo i18n infrastructure
- **Breaking changes**: None
