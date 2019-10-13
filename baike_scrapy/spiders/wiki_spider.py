# -*- coding: utf-8 -*-
import re
import os
import codecs
from opencc import OpenCC
from bs4 import BeautifulSoup
from scrapy import Request
from baike_scrapy.items import *
from scrapy.selector import Selector


class WikiSpiderSpider(scrapy.Spider):
    name = 'wiki_spider'
    allowed_domains = ['wikipedia.tw.wjbk.site']
    start_urls = [
        'https://wikipedia.tw.wjbk.site/baike-%E5%8C%97%E4%BA%AC%E8%88%AA%E7%A9%BA%E8%88%AA%E5%A4%A9%E5%A4%A7%E5%AD%A6']

    root_path = './data/'
    visited_urls = set()
    cc = OpenCC('t2s')   # 繁体字转简体字设置，维基中文为繁体字

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.wiki_parse)

    def wiki_parse(self, response):
        # self.save_page_content(response.body) # 保存获取的词条页面信息
        self.parse_page_content(response.body)  # 保存解析的info框内容

        soup = BeautifulSoup(response.body, 'lxml')
        links = soup.find_all('a', href=re.compile('/baike-%'))
        for link in links:
            if link not in self.visited_urls and len(self.visited_urls) < 100:
                yield Request(link["href"], callback=self.wiki_parse)
                self.visited_urls.add(link["href"])
                print('index: %d, visit %s' % (len(self.visited_urls), link["href"]))

        # self.get_wiki_info(response.body)  # 页面解析结果存入item，返回使用pipline存入neo4j

    def get_wiki_info(self, content):
        """
        :param content:
        :return:
        :将维基词条页面Info框内信息、词条描述、词条标签解析并放入item
        """
        selector = Selector(text=content)
        title = self.cc.convert(''.join(selector.xpath('//h1/text()').extract()).replace('/', ''))
        names = selector.xpath('//dt[contains(@class,"basicInfo-item name")]').extract()
        values = selector.xpath('//dd[contains(@class,"basicInfo-item value")]').extract()
        item = GraphNode()
        item['name'] = title
        item['props'] = {}
        for i, name in enumerate(names):
            temp = Selector(text=name).xpath('//dt/text()|//dt/a/text()').extract()
            name = ''.join(temp).replace('\n', '')
            name = self.cc.convert(''.join(name.split()))
            temp = Selector(text=values[i]).xpath('//dd/text()|//dd/a/text()').extract()
            value = ''.join(temp).replace('\n', '')
            if name != '' and value != '':
                item['props'][name] = self.cc.convert(value)

        # 获取词条描述信息
        descs = selector.xpath('//div[@id="mw-content-text"]/div[@class="mw-parser-output"]').extract()
        description = ''
        for desc in descs:
            desc1 = Selector(text=desc).xpath(
                '//div[@class="mw-parser-output"]/text()'
                '|//div[@class="mw-parser-output"]/b/text()'
                '|//div[@class="mw-parser-output"]/a/text()').extract()
            tmp = self.cc.convert(''.join(desc1).replace('\n', ''))
            description += tmp
        item['props']['词条描述'] = description

        # 获取词条标签
        labels = selector.xpath('//div[@id="mw-normal-catlinks"]/ul/li/a/text()').extract()
        label = self.cc.convert('，'.join(labels).replace('\n', '').replace(' ', ''))
        item['props']['词条标签'] = label

        return item

    def parse_page_content(self, content):
        """
        :param content:
        :return:
        :将维基词条页面信息解析并保存为txt文件
        :主要解析三部分信息：1.info框，2.词条描述，3.词条标签
        """
        selector = Selector(text=content)

        # 获取info框信息
        tr_cons = selector.xpath('//table[@class="infobox vcard"]/tbody/tr').extract()

        lines = ''
        for tr_con in tr_cons:
            temp = Selector(text=tr_con).xpath('//th/text()|//th//a/text()').extract()
            name = ''.join(temp).replace('\n', '')
            name = self.cc.convert(''.join(name.split()))
            temp = Selector(text=tr_con).xpath('//td/text()|//td//span/text()|//td//a/text()').extract()
            value = ''.join(temp).replace('\n', '')
            if name != '' and value != '':
                lines += name + '$$' + self.cc.convert(value) + '\n'

        # 获取词条描述信息
        descs = selector.xpath('//div[@id="mw-content-text"]/div[@class="mw-parser-output"]').extract()
        description = ''
        for desc in descs:
            desc1 = Selector(text=desc).xpath(
                '//div[@class="mw-parser-output"]/text()'
                '|//div[@class="mw-parser-output"]/b/text()'
                '|//div[@class="mw-parser-output"]/a/text()').extract()
            tmp = self.cc.convert(''.join(desc1).replace('\n', ''))
            description += tmp
        lines += '词条描述' + '$$' + description + '\n'
        # 获取词条标签
        labels = selector.xpath('//div[@id="mw-normal-catlinks"]/ul/li/a/text()').extract()
        label = self.cc.convert('，'.join(labels).replace('\n', '').replace(' ', ''))
        lines += '词条标签' + '$$' + label + '\n'

        # 存储信息
        path = os.path.join(self.root_path, 'wiki_infos')  # 创建文件存放路径
        if not os.path.exists(path):
            os.mkdir(path)
        title = self.cc.convert(''.join(selector.xpath('//h1/text()').extract()).replace('/', ''))
        f = codecs.open(os.path.join(path, title + '.txt'), 'w', encoding='utf-8')
        f.write(lines)
        f.close()

    def save_page_content(self, content):
        """
        :param content: response.body
        :return: None
        :将爬取的页面内容保存到磁盘
        """
        selector = Selector(text=content)
        title = selector.xpath('//title/text()').extract()[0]  # 获取文件标题
        path = os.path.join(self.root_path, 'wiki_pages')  # 创建文件存放路径
        if not os.path.exists(path):
            os.mkdir(path)
        f = codecs.open(os.path.join(path, title + '.html'), 'w', encoding='utf-8')
        f.write(content.decode('utf-8', errors='ignore'))
        f.close()
