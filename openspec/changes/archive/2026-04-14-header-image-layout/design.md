## Context

The `news.article` model displays a `header_image` field in both kanban and form views. Currently:
- Kanban: Full-width image with `aspect-ratio:1/1` above card content
- Form: Image in right column with label, alongside `scrape_date` field

The standard Odoo pattern for kanban cards with images (e.g., `res.partner`) uses a flex-row layout with the image as a small aside on the right.

## Goals / Non-Goals

**Goals:**
- Kanban: Small square image (64x64) in top-right corner using Odoo 18 flex-row card pattern
- Form: All metadata fields in left column, header image alone in right column without label
- Maintain existing functionality (image display, visibility conditions)

**Non-Goals:**
- Changing image storage or processing logic
- Modifying the `newsfeed` module's inherited views
- Adding new fields or model changes

## Decisions

### 1. Kanban Card Layout

**Decision:** Use Odoo 18's `flex-row` card class with `<main>` and `<aside>` elements.

**Rationale:** This is the standard Odoo 18 pattern for cards with side images (seen in OCA web modules). It provides:
- Responsive layout
- Proper alignment
- Consistent with Odoo's design system

**Implementation:**
```xml
<t t-name="card" class="flex-row">
    <main class="flex-grow-1">
        <!-- content -->
    </main>
    <aside t-if="record.header_image.raw_value" class="ms-2">
        <field name="header_image" widget="image" 
               options="{'size': [64, 64]}"/>
    </aside>
</t>
```

### 2. Form View Group Layout

**Decision:** Move all fields to left `<group>`, use right `<group>` only for image with `nolabel="1"`.

**Rationale:** This keeps related metadata together and gives the image its own space without awkward label placement.

**Implementation:**
```xml
<group>
    <group>
        <field name="source_id"/>
        <field name="date"/>
        <field name="url" widget="url"/>
        <field name="scrape_date"/>
    </group>
    <group>
        <field name="header_image" widget="image" nolabel="1"
               invisible="not header_image"
               options="{'size': [300, 300]}"/>
    </group>
</group>
```

## Risks / Trade-offs

**[Risk]** Kanban cards may look empty if many articles lack header images  
→ Acceptable: cards still show source, date, and title which is sufficient

**[Risk]** Image size (64x64) may be too small for detail  
→ Acceptable: kanban is for overview; users click through to form for details

**[Trade-off]** Right column empty when no image in form view  
→ Acceptable: this is the requested behavior and keeps layout consistent
