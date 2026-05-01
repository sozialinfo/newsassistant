# Article stages
- When the module ``newsassistant`` is installed, create the following article stages: New, Shortlist, Published (collapsed), Discarded (collapsed)
- In the module  ``newsassistant`` add the confiugraiton to define the stage for new arrticles
- In the module ``newsassistant_blog`` add the configuration to defined stages for human intervention needed (shortlist) and automatically published (published)
- When the module ``newsassistant_blog`` is installed, check if the stanard stages for shortlist and published are present. if yes, link them in the settings. if not, create them and link them in the settings

# Auto-Create blog
- When the module ``newsassistant_blog`` is installed, create a new blog "News" and add it as default in the settings




# Receiving E-Mail 
- Add a new module ``newsassistant_email``
- Using the odoo standard pattern for inbound e-mail, add a new alias ``newsassistant``
- The e-mail alias must be configurable
- When an e-mail is received
    - The module checks if a news source for the domain of the sender is defined
    - If not, a new news source is created
    - A new news article is created, with the e-mail body as the content
    - The log must be filled in the news source, using the same pattern as when scraping from a website

# Newsletter
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

# Digest
- If an article is discarded during digest due to misfit with the content strategy, the reasoning is not visible. Make sure to always show the Blog Tab, no matter the digest status.

# Merge Settings
- The settings for the News Assistant must all appear under one single menu in the settings, no matter if the module is actually a submodule.