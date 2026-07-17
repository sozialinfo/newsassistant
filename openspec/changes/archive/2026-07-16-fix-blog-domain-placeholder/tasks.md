## 1. Code Changes

- [x] 1.1 In `_generate_teaser()`: Update the AI prompt example to remove `{domain}` and `→` from the `read_more` example format
- [x] 1.2 In `_create_blog_post()`: Add `{domain}` substitution in the AI-generated `read_more` text with the actual source domain
- [x] 1.3 In `_create_blog_post()`: Style the source link as a primary button (`class="btn btn-primary"`)
- [x] 1.4 In `_create_blog_post()`: Remove the `→` symbol from the English fallback `read_more` text

## 2. Test Updates

- [x] 2.1 Update test expectations in `test_digest_pipeline.py` to match the new link format (no `→`, domain substitution)

## 3. Spec Update

- [x] 3.1 Update `openspec/specs/blog-publishing/spec.md` with the modified requirements for the new link format