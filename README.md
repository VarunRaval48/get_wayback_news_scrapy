
# Get Wayback news using Scrapy

This is a scrapy (python3) project.

The task of this project is to search for articles on any given news website within any given date range in the past. For example, search for news articles appeared on website nytimes.com during London Olympics 2012 (27 July to 12 August 2012).

### To search for articles of a given domain:
  1. Initialize global variables of class `NytimesSpider` in file scrapy_news/spiders/articles_spiders.py
  2. Make an instance of class `AccessInfo` with required information in init method of class `NytimesSpider`
  4. AccessInfo asks for a method that parses given html page and provide page info (Look at `nytimes_page_info`). Reason for that is given below.
  5. To run this project, go to scrapy_news/spiders and run command `scrapy crawl articles`.

### About Crawler:

Wayback machine stores snapshots of any given website on any given day in the past.

Provided a domain name and a date range, we can have all snapshots of given domain taken by Wayback machine on given date range (look at `get_home_page_urls` method in scrapy_news/spiders/wayback_util.py)

I have used [Beautifulsoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) to parse html page.
Given a home page (snapshot of home page of domain name), I look at appropriate `a` tags and extract urls.

Task to detect whether a page is an article is different for each domain. For example, for articles on nytimes.com, almost all the articles has `meta` tag with attributes `name=PT` and `content=Article`. For theguardian.com, this may be different. Hence, class `AccessInfo` asks for a methods that identifies whether a page is a proper page, is article and publication date of the article (if an article). Look at method `nytimes_page_info` for an example.

Similarly, task to look for story content is also different for different domains. For nytimes.com, one can look for string in `p` tag within `div id='articleBody'` tag. This task is not included in this project. This task can be done as a different process to reduce the overhead.