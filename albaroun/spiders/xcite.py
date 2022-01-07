# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from scrapy.http import TextResponse
import json, re
from scrapy.conf import settings

class JarirSpider(scrapy.Spider):
    name = 'xcite'
    # allowed_domains = ['http://www.jarir.com']
    start_urls = ['https://www.xcite.com.sa/']
    if settings.get("ARABIC_SETTING"):
        start_urls = ['https://www.xcite.com.sa/ar/']
        local_option = 'ar_SA'


    listing_page = None #"https://saudi.souq.com/sa-en/tote/handbags-472/a-t/s/"
    item_totalurls = []
    count = 0
    mysql_update = False
    if settings.get("MYSQL_ENABLE") and settings.get("MYSQL_ENABLE") != "False" and settings.get("MYSQL_UPDATE") == True:
        mysql_update = True

    def parse(self, response):
        if self.listing_page:
            yield response.follow(self.listing_page, callback=self.parse_listing)
        else:
            parents = response.xpath('//li[contains(@class, " parent parent-sub")]')
            for parent in parents:
                category = parent.xpath('./a/span/text()').extract_first()
                sub_parents = parent.xpath('.//li[contains(@class, "level1 groups item")]')
                for sub_parent in sub_parents:
                    sub_category = sub_parent.xpath('./a/span/text()').extract_first()
                    cateogy_url = sub_parent.xpath('.//div[@class="groups-wrapper"]/ul/li[contains(@class,"level") and not (contains(@class,"first"))]/a')
                    for a_url in cateogy_url:
                        url = a_url.xpath('./@href').extract_first()
                        sub_category = sub_category + '/' + a_url.xpath('./span/text()').extract_first()
                        yield response.follow(url, callback=self.parse_listing, meta={'category':category, 'sub_category':sub_category})
                        # break

    def parse_listing(self, response):
        item_li_tags = response.xpath('//div[contains(@class, "product-item")]')
        for item_li in item_li_tags:
            item_url = item_li.xpath('.//span[@class="product-name"]/a/@href').extract_first()
            id = item_li.xpath('.//button[@class="button mt-tooltip show-quickview"]/@data-id').extract_first()
            name = item_li.xpath('.//span[@class="product-name"]/a/text()').extract_first().strip()
            brand = name.split(' ')[0]
            ean = ''
            discount = item_li.xpath('.//div[@class="save-percent-container"]/label/text()').extract_first()
            # price = item_li.xpath('.//span[@class="finalprice"]/text()').re('[.\d]*[,\d]+')[0]
            price = item_li.xpath('.//meta[@itemprop="price"]/@content').extract_first()
            old_price = item_li.xpath('.//span[@class="beforeprice"]/text()').extract_first()
            if old_price:
                old_price = old_price.strip()
            item = dict(
                # id = id,
                brand_name = self.del_sp_char(brand),
                category = self.del_sp_char(response.meta['category']),
                # product__manufacturer = response.xpath('//*[@class="product__manufacturer"]/text()').extract_first(),
                ean = id,
                name = self.del_sp_char(name),
                discount = discount,
                image_url = response.xpath('//span[@class="front margin-image"]/img/@src').extract_first(),
                currency = 'SAR',
                price = price,
                old_price = old_price,
                url = item_url,
                # title = name,
                found_on = response.url,
                sub_category = self.del_sp_char(response.meta['sub_category']),
            )

            item["specs"] = ''
            yield item

        next_url = response.xpath('//a[@class="next i-next"]/@href').extract_first()
        if next_url:
            yield Request(next_url, callback=self.parse_listing, meta={'category':response.meta['category'], 'sub_category':response.meta['sub_category']})


    def del_sp_char(self, str_val):
        if str_val:
            return str_val.replace("'", "`")
        else:
            return str_val