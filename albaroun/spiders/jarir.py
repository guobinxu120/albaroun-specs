# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from scrapy.http import TextResponse
import json, re
from scrapy.conf import settings

class JarirSpider(scrapy.Spider):
    name = 'jarir'
    # allowed_domains = ['http://www.jarir.com']
    start_urls = ['http://www.jarir.com/sa-en/']
    listing_page = None #"https://saudi.souq.com/sa-en/tote/handbags-472/a-t/s/"
    item_totalurls = []
    count = 0
    mysql_update = False
    if settings.get("MYSQL_ENABLE") and settings.get("MYSQL_ENABLE") != "False" and settings.get("MYSQL_UPDATE") == True:
        mysql_update = True

    if settings.get("ARABIC_SETTING"):
        start_urls = ['http://www.jarir.com/']

    def parse(self, response):
        if self.listing_page:
            yield response.follow(self.listing_page, callback=self.parse_listing)
        else:
            menu_tags = response.xpath('//div[@id="custommenu"]/div[contains(@id, "popup")]')
            for menu in menu_tags:
                menu_id = menu.xpath('./@id').extract_first().replace('popup', '')
                category = response.xpath('//div[@id="menu{}"]/a/text()'.format(menu_id)).extract_first().strip()
                a_urls = menu.xpath('.//a[@class="menu-desktop__link level1"]')
                for a_url in a_urls:
                    url = a_url.xpath('./@href').extract_first()
                    sub_category = a_url.xpath('./text()').extract_first()
                    yield response.follow(url, callback=self.parse_listing, meta={'index':1, 'category':category, 'sub':sub_category})
                #     break
                # break

    def parse_listing(self, response):
        current_page = response.meta['index']

        try:
            body_json = json.loads(response.body)
            response = TextResponse(url=response.url,
                                body=str(body_json),
                                encoding='utf-8')
        except Exception as e:
            pass

        item_li_tags = response.xpath('//ul[contains(@class, "products-grid")]/li')
        return_flag = False
        for item_li in item_li_tags:
            url = item_li.xpath('.//a[@class="product-image"]/@href').extract_first()
            if not url in self.item_totalurls:
                break
            else:
                return_flag = True
                break

        if not return_flag :
            for item_li in item_li_tags:
                item_url = item_li.xpath('.//a[@class="product-image"]/@href').extract_first()
                self.item_totalurls.append(item_url)

                # if self.mysql_update:
                name = item_li.xpath('.//h3[contains(@class, "product-name")]/a/@title').extract_first()
                brand = re.findall("brand   : '(.+?)'",item_li.xpath('.//h3[contains(@class, "product-name")]/a/@onclick').extract_first())[0]
                if brand =='Non Branded':
                    brand = None

                ean = re.findall("id      : '(.+?)'",item_li.xpath('.//h3[contains(@class, "product-name")]/a/@onclick').extract_first())[0]

                category = response.meta['category']
                price = item_li.xpath('.//*[@itemprop="price"]/@content').extract_first()
                old_price = None
                discount = None
                if not price:
                    price = ''.join(item_li.xpath('.//span[contains(@id, "product-price")]/text()').extract()).strip()
                    old_price = ''.join(item_li.xpath('.//span[contains(@id, "old-price")]/text()').extract()).strip()
                    discount = item_li.xpath('.//span[contains(@class, "gift-summary__icon-amount")]/text()').extract_first().strip()

                item = dict(
                    brand_name = self.del_sp_char(brand),
                    category = self.del_sp_char(category),
                    ean = ean,
                    name = self.del_sp_char(name),
                    discount = discount,
                    price = price,
                    old_price = old_price,
                    url = item_url,
                    image_url = item_li.xpath('.//img[contains(@id, "product-collection-image")]/@data-src').extract_first(),
                    currency = 'SAR',
                    found_on = response.url,
                    sub_category = self.del_sp_char(response.meta['sub'])
                )
                yield item
                # else:
                #     yield Request(item_url, callback=self.parse_specs, meta={'category':response.meta['category'], 'category_url':response.url, 'sub':response.meta['sub']})

            if len(item_li_tags) >= 20:
                next_url = str(response.url.split('?')[0]) + '?is_ajax=1&p=' + str(current_page+1) + '&is_scroll=1'
                yield Request(next_url, callback=self.parse_listing, meta={'index': current_page+1, 'category':response.meta['category'], 'sub':response.meta['sub']})

    def parse_specs(self, response):
        brand = re.findall("brand   : '(.+?)'",response.body)[0]
        if brand =='Non Branded':
            brand = None
        ean = response.xpath('//*[@class="product__manufacturer"]/text()').extract_first()
        if ean:
            ean = ean.split(':')[-1]

        price = response.xpath('//*[@itemprop="price"]/@content').extract_first()
        if not price:
            prices = response.xpath('//p[@class="special-price"]/span[@class="price"]/text()').extract()
            price = prices[1]

        old_price = None
        old_prices = response.xpath('//p[@class="old-price"]/span[@class="price"]/text()').extract()
        if old_prices and len(old_prices) > 1:
            old_price = old_prices[1]

        discount = response.xpath('//*[@class="gift-summary__icon-amount"]/text()').extract_first()
        if discount:
            discount = discount.strip()

        item = dict(
                # id = response.xpath('//*[@itemprop="productID"]/text()').extract_first().strip(),
                brand_name = self.del_sp_char(brand),
                category = self.del_sp_char(response.meta['category']),
                # product__manufacturer = response.xpath('//*[@class="product__manufacturer"]/text()').extract_first(),
                ean = ean,
                name = self.del_sp_char(response.xpath('//*[@class="product__name"]/text()').extract_first().strip()),
                discount = discount,
                image_url = response.xpath('//img[@class="cloudzoom"]/@src').extract_first(),
                currency = 'SAR',
                price = price,
                old_price = old_price,
                url = response.url,
                # title = response.xpath('//*[@class="product__name"]/text()').extract_first().strip(),
                found_on = response.meta['category_url'],
                sub_category = self.del_sp_char(response.meta['sub'])
            )

        specs = {}
        li_speces = response.xpath('//div[@id="specifications"]//li[@class="product-attributes__item"]')
        for li in li_speces:
            key = li.xpath('.//*[@class="product-attributes__label"]/text()').extract_first().strip()
            val = li.xpath('.//*[@class="product-attributes__value"]/text()').extract_first().strip()
            if key:
                term = key.lower().replace(" ", "_").replace("`", "'")
                # item[u"specs_{}".format(term)] = val
                specs[key] = val


        item["specs"] = self.del_sp_char(json.dumps(specs, ensure_ascii=False))
        # self.count += 1
        # print(self.count)
        yield item

    def del_sp_char(self, str_val):
        if str_val:
            return str_val.replace("'", "`")
        else:
            return str_val




