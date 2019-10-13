# -*- coding: utf-8 -*-
import re
import os
import codecs
from bs4 import BeautifulSoup
from scrapy import Request
from baike_scrapy.items import *
from scrapy.selector import Selector


class HudongSpider(scrapy.Spider):
    name = 'hudong_spider'
    allowed_domains = ['baike.com']
    start_urls = ['http://www.baike.com/wiki/%E5%8C%97%E4%BA%AC%E8%88%AA%E7%A9%BA%E8%88%AA%E5%A4%A9%E5%A4%A7%E5%AD%A6']

    root_path = './data/'
    visited_urls = set()
    url_pattern = 'http://baike.com{}'

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.hudong_parse)

    def hudong_parse(self, response):
        # self.save_page_content(response.body)  # 保存获取的词条页面信息
        self.parse_page_content(response.body)  # 保存页面解析结果

        soup = BeautifulSoup(response.body, "lxml")
        links = soup.find_all("a", href=re.compile('/wiki/*'))
        for link in links:
            if 'www.baike.com' not in link['href']:
                link['href'] = self.url_pattern.format(link['href'])
            if link not in self.visited_urls and len(self.visited_urls) < 100:
                yield Request(link["href"], callback=self.hudong_parse)
                self.visited_urls.add(link["href"])
                print('index: %d, visit %s' % (len(self.visited_urls), link["href"]))

        # yield self.get_hudong_info(response.body)  # 页面解析结果存入item，返回使用pipline存入neo4j

    def get_hudong_info(self, content):
        """
        :param content:
        :return:
        :将互动词条页面Info框内信息、词条描述、词条标签解析并放入item
        """
        selector = Selector(text=content)
        title = ''.join(selector.xpath('//h1/text()').extract()).replace('/', '')
        td_cons = selector.xpath("//div[@id='datamodule']//table//tr//td").extract()
        item = GraphNode()
        item['name'] = title
        item['props'] = {}
        for td_con in td_cons:
            temp = Selector(text=td_con).xpath('//strong/text()').extract()
            name = ''.join(temp).replace('\n', '')
            name = name[:-1].strip()
            temp = Selector(text=td_con).xpath('//span/text()').extract()
            value = ''.join(temp).replace('\n', '')
            if value is not None:
                item['props'][name] = value

        # 获取词条描述信息
        desc = selector.xpath("//div[@id='unifyprompt']//p//text()").extract()
        description = re.sub('\[[0-9]+\]', '', ''.join(desc).replace('\n', ''))
        item['props']['词条描述'] = description

        # 获取词条标签
        labels = selector.xpath("//div[@class='place']//p//a//text()").extract()
        label = ','.join(labels).replace('\n', '').replace(' ', '')
        item['props']['词条标签'] = label

        return item

    def parse_page_content(self, content):
        """
        :param content:
        :return:
        :将互动词条页面Info框内信息解析并保存为txt文件
        :主要解析三部分信息：1.info框，2.词条描述，3.词条标签
        """

        # 获取info框信息
        selector = Selector(text=content)
        td_cons = selector.xpath("//div[@id='datamodule']//table//tr//td").extract()
        lines = ''
        for td_con in td_cons:
            temp = Selector(text=td_con).xpath('//strong/text()').extract()
            name = ''.join(temp).replace('\n', '')
            name = name[:-1].strip().replace(' ', '')
            temp = Selector(text=td_con).xpath('//span/text()|//span/a/text()').extract()
            value = ''.join(temp).replace('\n', '')
            if name != '' and value != '':
                lines += name + '$$' + value + '\n'

        # 获取词条描述信息
        desc = selector.xpath("//div[@id='unifyprompt']//p//text()").extract()
        description = re.sub('\[[0-9]+\]', '', ''.join(desc).replace('\n', ''))
        lines += '词条描述' + '$$' + description + '\n'

        # 获取词条标签
        labels = selector.xpath("//div[@class='place']//p//a//text()").extract()
        label = ','.join(labels).replace('\n', '').replace(' ', '')
        lines += '词条标签' + '$$' + label + '\n'

        # 存储信息
        path = os.path.join(self.root_path, 'hudong_infos')  # 创建文件存放路径
        if not os.path.exists(path):
            os.mkdir(path)
        title = ''.join(selector.xpath('//h1/text()').extract()).replace('/', '')
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
        title = selector.xpath('//title/text()').extract()[0].strip()  # 获取文件标题
        path = os.path.join(self.root_path, 'hudong_pages')  # 创建文件存放路径
        if not os.path.exists(path):
            os.mkdir(path)
        f = codecs.open(os.path.join(path, title + '.html'), 'w', encoding='utf-8')
        f.write(content.decode('utf-8', errors='ignore'))
        f.close()
