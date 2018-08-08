# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ScrapyNewsPipeline(object):
  def process_item(self, item, spider):
    return item


class SavepagePipeline(object):
  # def __init__(self):
  # self.saved_pages = set()

  def process_item(self, item, spider):
    spider.state['saved_pages'] = spider.state.get('saved_pages', set())

    pub_date = item['pub_date']
    access_info = item['access_info']
    r_addr = item['addr']
    page = item['page']
    page_type = item['page_type']
    if page_type is None:
      page_type = 'NOTYPE'

    # save article if appropriate
    # check for publication dateget_page_info
    if pub_date is not None:
      if pub_date < access_info.allowed_start_date or pub_date > access_info.allowed_end_date:
        return
    else:
      pub_date = '????????'

    # remove string after ? in address (they indicate sections)
    # TODO check here whether things after ? change pages
    r_addr = r_addr.split("?")[0]

    article_name = '{}_{}_{}'.format(pub_date, page_type, r_addr)

    if article_name not in spider.state['saved_pages']:
      spider.state['saved_pages'].add(article_name)
      access_info.save_article(page, str(pub_date), r_addr,
                               access_info.dir_name, article_name)