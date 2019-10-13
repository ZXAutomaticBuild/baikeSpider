# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from baike_scrapy.items import *
from py2neo import Graph, Node


class GraphNodePipline(object):
    """
    :页面解析结果作为节点存入neo4j数据库
    :使用时请放开settings.py文件中 ITEM_PIPELINES字段中该pipline的注释
    """
    def __init__(self):
        self.graph = Graph(
            "http://localhost:7474",
            username="neo4j",
            password="123456xz+"
        )

    def process_item(self, item, spider):
        if isinstance(item, GraphNode):
            self.add_entity(item['name'], item['props'])

    def add_entity(self, name1, attrs):
        a = Node(name1, name=name1, **attrs)
        self.graph.create(a)
