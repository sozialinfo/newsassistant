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





# Strategy Digest
With this new feature, news can be screened for relevance to the long term strategy of the organisation.

- Add a new module ``newsassistant_strategy_digest``
- In this new module, a many-to-many field ``strategy_digest`` is added to the news article, which allows to add labels. Use the odoo standard pattern
- In the configuration, an admin user can define labels
- In the configuration, an admin user can define a Strategy Digest prompt which returns labels for a specific article
- The user can copy/paste the full strategy of the organisation and the module then suggests a strategy digest prompt and the labels
- In the kanban board, add the possibility to group by strategy digest label
- Add a new model strategy_digest which contains the digest for a certain period. It contains links to the selected articles as well as a strategy brief (HTML editor)
- Add a new menu "Strategy Digest". It shows a list of strategy digest records.
- When adding a new digest, the module creates a new brief, using AI for a selected period. It reads articles wich are deemed strategy-relevant and then renders a strategy brief as HTML in the language of the user, with an executive summary and a more detailled text, referencing the origianl sources of new articles where applicable. The strategy brief can be freely edited and downloaded as PDF. It should be no longer than 2 A4-pages.


# Translation
Make sure all terms are translated to German