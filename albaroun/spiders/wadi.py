# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from scrapy.http import TextResponse
import json, re
from scrapy.conf import settings

class WadiSpider(scrapy.Spider):
    name = 'wadi'
    # allowed_domains = ['http://www.jarir.com']
    start_urls = ['https://en-sa.wadi.com/']
    local_option = 'en_SA'
    if settings.get("ARABIC_SETTING"):
        start_urls = ['https://ar-sa.wadi.com/']
        local_option = 'ar_SA'

    listing_page = None #"https://saudi.souq.com/sa-en/tote/handbags-472/a-t/s/"
    item_totalurls = []
    count = 0
    mysql_update = False
    if settings.get("MYSQL_ENABLE") and settings.get("MYSQL_ENABLE") != "False" and settings.get("MYSQL_UPDATE") == True:
        mysql_update = True

    headers = {
                    'content-type': 'application/json',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
                    'n-locale': local_option,
                    'n-platform': 'web',
                    'n-context': 'large',
                    'n-device': 'desktop'
                }

    def parse(self, response):
        urls = []
        if self.listing_page:
            yield response.follow(self.listing_page, callback=self.parse_listing)
        else:
            p = re.compile('window.nav=(.*)"icon":null,"children":null}]}]')
            str_data = p.findall(response.body)[0] + '"icon":null,"children":null}]}]}]}'
            category_data = json.loads(str_data)

            for cat1 in category_data['menu']:
                if not 'children' in cat1.keys(): continue
                category = cat1['title']
                for cat2 in cat1['children']:
                    if not 'children' in cat2.keys() or cat2['children'] == None : continue
                    sub_category = cat2['title']
                    for cat3 in cat2['children']:
                        if cat3['url']:
                            sub_category = sub_category +'/' + cat3['title']
                            yield Request(self.start_urls[0] + "api/sawa/v1/u" + cat3['url'], callback=self.parse_listing, meta = {'category' :category, 'sub_category':sub_category}, headers=self.headers)

    def parse_listing(self, response):
        json_data = json.loads(response.body)
        for item_data in json_data['data']:
            item = dict(
                # id = None,
                brand_name = self.del_sp_char(item_data['brand']['name']),
                category = self.del_sp_char(response.meta['category']),
                # product__manufacturer = response.xpath('//*[@class="product__manufacturer"]/text()').extract_first(),
                ean = item_data['sku'],
                name = item_data['name'].replace("'", "`"),
                discount = item_data['discount'],
                image_url = 'https://b.wadicdn.com/product/{}/1-product.jpg'.format(item_data['imageKey']),
                currency = 'SAR',
                price = item_data['price'],
                old_price = item_data['offerPrice'],
                url = self.start_urls[0] + item_data['link'],
                # title = item_data['name'],
                found_on = response.url.replace('/api/sawa/v1/u', ''),
                sub_category = self.del_sp_char(response.meta['sub_category']),
            )
            if item_data['highlights'] and len(item_data['highlights']) > 0:
                item["specs"] = '\n'.join(item_data['highlights']).replace("'", "`")
            else:
                item["specs"] = ''
            yield item

        if json_data['pages'] != json_data['search']['page']:
            current = int(json_data['search']['page'])
            if 'page=' in response.url:
                next_url = re.sub('page=\d+', 'page='+str(current+1), response.url)
            else:
                next_url = response.url + "&page=" + str(current+1)
            yield Request(next_url, callback=self.parse_listing, meta = {'category' :response.meta['category'], 'sub_category':response.meta['sub_category']}, headers=self.headers)

    def del_sp_char(self, str_val):
        if str_val:
            return str_val.replace("'", "`")
        else:
            return str_val







