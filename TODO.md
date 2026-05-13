# Snapshot
- Remove Chatter from Snapshot

# Blog Result
- After processing an article for blog relevance, the user must see the result: irrelevant (move to verworfen), uncertain (move to shortlist), matching (create blog post and move to published)
- The reasoning must always be visible to understand why an article was selected (nor not)



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

# Translation
- Make sure all terms accross all modules are translated to German and French.
- Make sure all visible prompts and prompt answers are in the langauge of the user triggering the action



# Logging
Refactor the logging to use the standard ir.logging model where possible.
- Please note: These modules are not used in production yet, so no migration is necessary

# Modular install
Use the same Odoo standard pattern as for other modules with submodules. In the settings, add checkboxes to add capatilities (e.g. automatically publish selected articles on own blog). When a capability is selected, the respective submodule is installed on save. Use the same pattern as Odoo standard also for uninstalls via settings.

# Prompts
Refactor all prompts embedded in code to be standalone MD files in the same directory as the PY file using the prompt. I want the prompts the be human editable.

# Cron-Job
I only want one single cron job, defined in the base module, which does _all_ the work. When it runs, it scrapes all the sources, creates articles and then also calls the follow-up actions defined in the sub-modules (e.g. strategy check, content relevance for blog post publishing, etc.). Make sure to keep the dependency tree clean and use an appropriate architectural patttern.



