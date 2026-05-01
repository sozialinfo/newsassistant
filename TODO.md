# Header Image
- In kanban view of an article, the header image is much too big. it must be a square at the right top corner. use the same pattern as the kanban card in res.partner
- in detail view of an article, the header image is placed awkwardly. in the header section, move all fields to the left column. use the right column only for the header picture, but witouht any label. if there is no header picture, the right column remains empty

# Blog
- move the tab ``teaser`` before the tab ``log``
- Rename the tab ``teaser`` to Blog
- In the Blog tab, add the digest state (move from the header), show the reasoning (why this is relevant for the blog, according to our content strategy), the teaser and the external link to the blog post

# Article stages
- When the module ``newsassistant`` is installed, create the following article stages: New, Shortlist, Published (collapsed), Discarded (collapsed)
- In the module  ``newsassistant`` add the confiugraiton to define the stage for new arrticles
- In the module ``newsassistant_blog`` add the configuration to defined stages for human intervention needed (shortlist) and automatically published (published)
- When the module ``newsassistant_blog`` is installed, check if the stanard stages for shortlist and published are present. if yes, link them in the settings. if not, create them and link them in the settings

# Auto-Create blog
- When the module ``newsassistant_blog`` is installed, create a new blog "News" and add it as default in the settings