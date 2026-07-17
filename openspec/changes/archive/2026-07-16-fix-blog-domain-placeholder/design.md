## Context

The `_create_blog_post()` method in `newsassistant_blog/models/news_article.py` generates the blog post content with a teaser and a link to the source article. The AI-generated `read_more` text may contain the literal string `{domain}` because the AI prompt includes it as an example placeholder. The code extracts the actual domain from the article URL but never substitutes it into the AI-generated text.

## Goals / Non-Goals

**Goals:**
- Replace `{domain}` in the AI-generated `read_more` text with the actual source domain
- Style the source link as a primary button (`btn btn-primary`)
- Remove the `→` symbol from the link text, prompt example, and fallback
- Update the AI prompt example to not include `{domain}` or `→`

**Non-Goals:**
- No changes to the AI model or prompt structure beyond the example format
- No changes to the teaser text itself
- No changes to the blog post creation logic beyond the content HTML

## Decisions

1. **Post-processing substitution** — Instead of modifying the AI prompt to include the actual domain (which would require the AI to correctly interpolate it), we substitute `{domain}` in the `read_more` text after AI generation. This is more robust because:
   - The AI may still output `{domain}` even if the prompt includes the actual domain
   - The substitution is a simple string replace that always works
   - The AI prompt example is cleaned up to not suggest `{domain}` or `→` as patterns

2. **Button styling** — Add `class="btn btn-primary"` to the `<a>` tag in the blog post content. This is standard Odoo CSS and works in blog posts.

3. **Remove `→`** — Remove the arrow from both the AI prompt example and the English fallback. The link text is self-explanatory without it.

## Risks / Trade-offs

- [Low] If the AI generates `read_more` text with `{domain}` in a context where it shouldn't be replaced (e.g., in a sentence like "visit {domain} for more"), the substitution will still happen. This is acceptable because `{domain}` is unlikely to appear naturally in generated text.
- [Low] Existing blog posts with the `→` symbol will not be retroactively updated. Only new posts will have the corrected format.