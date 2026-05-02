# Mass Mailing
- Add a new module ``newsassistant_mass_mailing``. The purpose of this module is to select news articles for publication in a newsletter. It depends on ``mass_mailing``
- On the news article, add a new flag ``newsletter_relevant``. It must be possible to set/unset this flag in the detail view, but also in the list view
- Add a new menu "Newsletter"
- Add a new menu "Newsletter > Selected Articles"
    - This menu shows a filtered list of articles which have the ``newsletter_relevant`` flag set, but are not yet linked to a newsletter
    - The user can also manually switch the filter to all articles which have the ``newsletter_relevant`` flag set and are linked to a newsletter or just "all" (the flag is set, no distiction whether linked to a newsletter or not)
- Add a new action "Add to Newsletter"
    - As a button on the detail view of an article
    - As an action on the list view of all articles
    - When clicked, a popup appears, where the user must select the newsletter where the news will be added to. In the same popup, it must be possible to create a new newsletter, either from a template or as a copy of an existing newsletter
    - In the selected newsletter, add a new section for each article, with the title, the digest blurb, the image (with a reasonable size) and the link back to the original source of the article. If there is no image, use just the blurb and adjust the layout. Use AI to find the proper placing within existing newsletters.


# Strategy UI
For the strategy.strategy, add a status "draft/active/archived", including a ribbon (not sure if this is the proper widget name, use the standard odoo pattern) in the top right corner of the detail view. Make sure the strategy can only be activated if the prompt is set. If the user tries to activate without the prompt, offer the action to create the prompt from the available documents (if there are documents attached). Move the "create prompt" button inside the tab with the prompt and rename the tab just "prompt". Add an explanation above the prompt what the purpose of this prompt is. The prompt itself must be HTML (only converted to MD "on the fly" when sending it to the LLM).


# Translation
- Make sure all terms accross all modules are translated to German and French.
- Make sure all visible prompts and prompt answers are in the langauge of the user triggering the action

# SmartButton
- Add a SmartButton (admin only) in news article to show the related snapshots

# Logging
Refactor the logging to use the standard ir.logging model
- Please note: These modules are not used in production yet, so no migration is necessary

# Modular install
Use the same Odoo standard pattern as for other modules with submodules. In the settings, add checkboxes to add capatilities (e.g. automatically publish selected articles on own blog). When a capability is selected, the respective submodule is installed on save. Use the same pattern as Odoo standard also for uninstalls via settings.

# UI for Blog and Stragety
I want to use the same UI pattern for blog and strategy_digest

In the article detail view
- Move everything related to Blog to the tab Blog (including the Button)
- Move everything related to Strategy to the tab Strategy (including the Button)
- Move then button to re-trigger the evaluation next to the evaluation state
- Make sure the evaluation state is displayed in the same way with the same language in both tabs
- Make sure the reasoning for the evaluation is displayed in the same way with the same language in both tabs
- The result for the blog is text (teaser) and for strategy the labels

# Raw Content
- In the snapshots, display the raw content as HTML and make it read-only
- Rename to just "Content"
- Rerder the tabs: Content first, then articles

# Blog Post
- When creating a blog post, the content must be in the language of the website, including the the "Read full article..." at the end
- If a website is available in multiple languages, use the odoo standard translation infrastructure (attention: It changed for Version 18) to add the translations for all languages

# Snapshot
For snapshots from websites, include the exact URL of the website in the snapshot

# Article Date
Make the date of an article mandatory. If the LLM cannot find a date, assume [today] as the article's date. When creating a new article in the GUI, automatically prefill the date with [today]