import os
import sys
import time

from datetime import datetime

import scrapy

from .util import get_date_format, get_page_addr, get_snapshot_number
from .wayback_util import get_home_page_urls, get_unique_addr, is_url_proper
from .newssite_util import nytimes_page_info, save_article, AccessInfo, nytimes_url
from ..items import PageItem

headers = {
    'DNT':
    '1',
    'Accept-Encoding':
    'gzip, deflate',
    'Accept-Language':
    'en-US,en;q=0.8',
    'Upgrade-Insecure-Requests':
    '1',
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
    'Accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Connection':
    'keep-alive',
}


# dir_name given without last slash
class NytimesSpider(scrapy.Spider):
  name = "articles"
  rotate_user_agent = True

  handle_httpstatus_list = [404]

  url, domain_name = "http://www.nytimes.com/", "nytimes.com"

  def __init__(self,
               year='2010',
               month='1',
               day='1',
               end_date='20100630',
               allowed_start_date='20100101',
               allowed_end_date='20180731',
               dir_name='./articles',
               *args,
               **kwargs):

    scrapy.Spider.__init__(self, *args, **kwargs)

    year = int(year)
    month = int(month)
    day = int(day)

    no_days = datetime.strptime(end_date, '%Y%m%d') - datetime.strptime(
        get_date_format(year, month, day), '%Y%m%d')
    no_days = no_days.days

    end_date = int(end_date)
    allowed_start_date = int(allowed_start_date)
    allowed_end_date = int(allowed_end_date)

    self.access_info = AccessInfo(
        year, month, day, no_days, end_date, allowed_start_date,
        allowed_end_date, NytimesSpider.url, NytimesSpider.domain_name,
        nytimes_page_info, nytimes_url, dir_name, save_article)
    # self.seen_pages = set()

  def start_requests(self):
    self.state['seen_pages'] = self.state.get('seen_pages', set())
    home_pages = get_home_page_urls(self.access_info)
    print(home_pages)
    for snap, urls in home_pages.items():
      for url in urls:
        self.state['seen_pages'].add(
            get_unique_addr(get_snapshot_number(url), ''))
        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

  def parse(self, response):
    url = response.request.url
    r_url = response.url
    snap = get_snapshot_number(r_url)
    addr = get_page_addr(r_url, self.access_info.domain_name)

    if (response.status == 404):
      r_url = r_url.split("?")[0]
      return scrapy.Request(url=r_url, headers=headers, callback=self.parse)

    # print(snap)
    if is_url_proper(url, r_url, self.access_info):
      if url != r_url:
        u_addr = get_unique_addr(snap, addr)
        if u_addr in self.state['seen_pages']:
          return

        self.state['seen_pages'].add(u_addr)

      page = response.body.decode('utf-8', 'ignore')
      soup, is_proper_page, pub_date_home, is_article, page_type, pub_date = \
        self.access_info.get_page_info(page, r_url)

      if not is_proper_page:
        return

      # if it is article then accept,
      # it not article and a page that is not within start and end date, ignore it
      # (as it will be seen by someone else, to ignore repetitive parsing)
      if is_article:
        yield PageItem(
            url=r_url,
            snap=snap,
            addr=addr,
            page=page,
            page_type=page_type,
            pub_date=pub_date,
            access_info=self.access_info)
      else:
        if pub_date_home is not None:
          if pub_date_home < self.access_info.start_date or pub_date_home > self.access_info.end_date:
            return
        else:
          # it is a home page and beyond start, end date
          snap_old_date = int(snap[:8])
          if snap_old_date < self.access_info.start_date or snap_old_date > self.access_info.end_date:
            return

        all_as = soup.find_all('a', href=True)

        for a_tag in all_as:
          href = str(a_tag['href'])
          # href = href.split("?")[0]

          if not self.access_info.check_url(href):
            continue

          addr = get_page_addr(href, self.access_info.domain_name)

          snap_new = get_snapshot_number(href)
          if snap_new is None:
            continue

          snap_date = int(snap_new[:8])

          # TODO check if second condition will ever happen (below)
          #  or snap_date > self.access_info.allowed_end_date
          if snap_date < self.access_info.allowed_start_date:
            continue

          if addr is not None:
            u_addr = get_unique_addr(snap_new, addr)

          # check whether url is in the set using page specific url name
          if addr is None or u_addr in self.state['seen_pages']:
            continue

          # print(u_addr)

          self.state['seen_pages'].add(u_addr)
          yield scrapy.Request(href, headers=headers, callback=self.parse)
