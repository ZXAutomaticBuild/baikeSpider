# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BaikeScrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class GraphNode(scrapy.Item):
    """
    :name neo4j节点名称，用于展示用
    :props neo4j节点各属性键值对
    """
    name = scrapy.Field()
    props = scrapy.Field()
