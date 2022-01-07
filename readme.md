## Run Instructions

### To Crawl the entire site:
scrapy crawl souq --nolog

### To Parse one listing page
scrapy crawl souq -a listing_page="https://saudi.souq.com/sa-en/tote/handbags-472/a-t/s/" --nolog

### --nolog
Having --nolog speeds things up, but if you want to see the items scroll as they are scraped just remove it


## Configuration
### Settings
Settings can be set inside `settings.py` 
All settings are self-explainatory but the most important ones are:

- Mysql username, password, and database
- Download Image Flag
- Image Path
- Cache Flag `HTTPCACHE_ENABLED`

### Cron: 
0 0 * * * (cd /path/to/project/ && scrapy crawl souq --nolog)

