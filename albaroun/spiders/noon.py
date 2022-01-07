# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from scrapy.http import TextResponse, FormRequest
import json, re
from scrapy.conf import settings

class JarirSpider(scrapy.Spider):
    name = 'noon'
    domains = ['https://www.noon.com/en-sa/']
    location_option = 'en-sa'

    start_urls = ['https://www.noon.com/_svc/catalog/api/u/']

    # if settings.get("ARABIC_SETTING"):
    #     domains = ['https://www.noon.com/ar-sa/']
    #     location_option = 'ar-sa'

    listing_page = None #"https://saudi.souq.com/sa-en/tote/handbags-472/a-t/s/"
    categoies = ['electronics', 'beauty', 'fashion', 'home-kitchen', 'sports-outdoors', 'toys', 'baby',
                 'automotive', 'tools-and-home-improvement', 'books', 'pet-supplies', 'office-supplies', 'music-movies-and-tv-shows']
    count = 0
    mysql_update = False
    headers = {
                    'content-type': 'application/json',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
                    'x-locale': location_option,
                    'x-platform': 'web',
                }

    formdata = {"brand":[],"category":["automotive"],"filterKey":[],"f":{},"sort":{"by":"popularity","dir":"desc"},"limit":'50',"page":'1'}

    if settings.get("MYSQL_ENABLE") and settings.get("MYSQL_ENABLE") != "False" and settings.get("MYSQL_UPDATE") == True:
        mysql_update = True

    def start_requests(self):
        for cat in self.categoies:
            if cat=="automotive":
                yield Request('https://www.noon.com/_svc/catalog/api/search',callback=self.parse, method="POST", body=json.dumps(self.formdata), headers=self.headers )
            else:
                yield Request(self.start_urls[0]+cat, callback=self.parse, headers=self.headers)
            # break

    def parse(self, response):

        if self.listing_page:
            yield response.follow(self.listing_page, callback=self.parse_listing)
        else:
            cat_data = json.loads(response.body)
            if cat_data['type'] == "static":
                if not 'sections' in cat_data['data'][0].keys():
                    return
                for cat1_data in cat_data['data'][0]['sections'][0]['sectionLinks']:
                    yield Request(response.url + cat1_data['url'], callback=self.parse, headers=self.headers)
                    # break
            else:
                for item_data in cat_data['hits']:
                    price = item_data['price']
                    old_price = None
                    discount = None
                    if item_data['sale_price']:
                        price = item_data['sale_price']
                        old_price = item_data['price']
                        discount = str(int((float(old_price) - float(price)) * 100 / float(old_price))) + "%"
                    category = cat_data['breadcrumbs'][0]['name']
                    if len(cat_data['breadcrumbs'])>1:
                        sub_category = cat_data['breadcrumbs'][-1]['name']
                    else:
                        sub_category = None

                    brand = item_data['brand']

                    if brand:
                        brand = brand.replace("'", "`")
                    item = dict(
                        # id = None,
                        brand_name = self.del_sp_char(brand),
                        category = self.del_sp_char(category),
                        # product__manufacturer = response.xpath('//*[@class="product__manufacturer"]/text()').extract_first(),
                        ean = item_data['sku'],
                        name = item_data['name'].replace("'", "`"),
                        discount = discount,
                        image_url = 'https://k.nooncdn.com/t_desktop-pdp-v1/' + item_data['image_key'] + '.webp',
                        currency = 'SAR',
                        price = price,
                        old_price = old_price,
                        url = self.domains[0] + item_data['url']+'/'+item_data['sku']+'/p/',
                        # title = item_data['name'],
                        found_on = self.domains[0] + cat_data['canonical_url'],
                        specs = None,
                        sub_category = self.del_sp_char(sub_category),
                    )
                    if self.mysql_update:
                        yield item
                    else:
                        item_url = 'https://www.noon.com/_svc/catalog/api/product/{}?shippingCountryCode=SA'.format(item_data['sku'])
                        yield Request(item_url,callback=self.final_specs, meta={'item':item}, headers=self.headers)

                if cat_data['nbPages'] != cat_data['search']['page']:
                    formdata = cat_data['search']
                    formdata['page'] = str(int(cat_data['search']['page'] ) + 1)
                    formdata['limit'] = str(cat_data['search']['limit'])

                    yield Request('https://www.noon.com/_svc/catalog/api/search',callback=self.parse, method="POST", body=json.dumps(formdata), headers=self.headers )


    def final_specs(self, response):
        data = json.loads(response.body)
        item = response.meta['item']
        specs = {}

        for spec in data['product']['specifications']:
            specs[spec['name']] = spec['value']

        item['specs'] = json.dumps(specs, ensure_ascii=False).replace("'", "`")

        yield item

    def del_sp_char(self, str_val):
        if str_val:
            return str_val.replace("'", "`")
        else:
            return str_val
