from scrapy import cmdline

# 放开注释即可执行相应的百科爬虫代码，每次仅能够执行一个爬虫
# cmdline.execute('scrapy crawl baidu_spider'.split())
# cmdline.execute('scrapy crawl hudong_spider'.split())
cmdline.execute('scrapy crawl wiki_spider'.split())
