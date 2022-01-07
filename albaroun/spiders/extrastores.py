# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from scrapy.http import TextResponse
import json, re, time
from urlparse import urljoin
from scrapy.conf import settings

class ExtrastoresSpider(scrapy.Spider):
    name = 'extrastores'
    # allowed_domains = ['http://www.extrastores.com/en-sa/']
    start_urls = ['http://excdn.azureedge.net/MegaMenu_en_sa.json']

    if settings.get("ARABIC_SETTING"):
        start_urls = ['http://excdn.azureedge.net/MegaMenu_ar_sa.json']

    listing_page = None #"https://saudi.souq.com/sa-en/tote/handbags-472/a-t/s/"
    item_totalurls = []
    category_urls = []
    count = 0
    use_selenium = False

    mysql_update = False
    if settings.get("MYSQL_ENABLE") and settings.get("MYSQL_ENABLE") != "False" and settings.get("MYSQL_UPDATE") == True:
        mysql_update = True

    def parse(self, response):
        if self.listing_page:
            yield response.follow(self.listing_page, callback=self.parse_listing)
        else:
            json_data = json.loads(response.body)
            for parent_item in json_data['Categories']:
                for cat1 in parent_item['Columns']:
                    for cat2 in cat1['Families']:
                        if not 'SubFamilies' in cat2.keys() or len(cat2['SubFamilies']) < 1:
                            self.category_urls.append(cat2['Link'])
                        else:
                            for cat3 in cat2['SubFamilies']:
                                self.category_urls.append(cat3['Link'])

            for url in self.category_urls:
                time.sleep(2)
                if '/products/' in url or '/promotions/' in url:
                    cat_final = url.split('/')[-1]
                    part_txt = url.split('/')[-2]
                    if part_txt == 'products':
                        url = url.replace(cat_final, 'CategoryProducts/' + cat_final)
                    elif part_txt == "promotions":
                        url = url.replace(cat_final, 'ProductsPageProducts/' + cat_final)
                    else:
                        url = url.replace(cat_final, 'ProductListingProducts/' + cat_final)
                    yield Request("http://www.extrastores.com" + url, callback=self.parse_listing)
                else:
                    final_str = url.split('-')[-1]
                    try:
                        final_int = int(final_str)
                        if final_int > 100 and len(final_str) > 5:
                            if not url in self.item_totalurls:
                                self.item_totalurls.append(url)
                                print("spec: " + url)
                                yield Request("http://www.extrastores.com" + url, callback=self.parse_specs, meta={'category_url':url})
                    except:
                        print ("gerneral: "+url)
                        yield Request("http://www.extrastores.com" + url, callback=self.parse_listing)
                    #     yield Request("http://www.extrastores.com/en-sa/search?page=1&q=%3bJuicer", callback=self.parse_listing)
                    # break


    def parse_listing(self, response):
        try:
            json_data = json.loads(response.body)
            items = json_data['Products']
            for item in items:
                url = item['GtmProductFriendlyUrl']
                image_url = item['ImageUrl']
                if self.mysql_update:
                    price = item['activeprice']
                    old_price = item['ProductPrice']
                    discount = item['SavingPercent'].replace('<span>', '').replace('<p>', '').replace('</span>', '').replace('</p>', '').strip()
                    item = dict(
                                discount = discount,
                                price = price,
                                old_price = old_price,
                                url = url
                            )
                    yield item
                else:
                    if not url in self.item_totalurls:
                        self.item_totalurls.append(url)
                        yield Request(urljoin(response.url, url), callback=self.parse_specs, meta={'category_url':response.url, 'image_url' : image_url})

            if int(json_data['MaxPage']) != 1 and json_data['CurrentPage'] != json_data['MaxPage']:
                if '&page=' in response.url:
                    baseurl = response.url.split('&page=')[0]
                    yield Request(baseurl + '&page=' + str(int(json_data['CurrentPage']) +1), callback=self.parse_listing)
                else:
                    yield Request(response.url + '&page=' + str(int(json_data['CurrentPage']) +1), callback=self.parse_listing)

        except:
            item_urls = response.xpath('//*[@class="productbox"]')
            if item_urls:
                for item_tag in item_urls:
                    print ("No_image: " +response.url)
                    item_url = item_tag.xpath('./a/@href').extract_first()
                    url = item_url.replace('javascript:gtm.traceProductClick("', '').split(',')[0].replace('"', '')
                    image_url = item_tag.xpath('.//img[contains(@class, "eXtraContentPlaceHolder_SearchUC")]/@src').extract_first()
                    if self.mysql_update:
                        price = item_tag.xpath('.//div[@class="price4"]/text()').extract_first()
                        old_price = item_tag.xpath('.//div[@class="oldprice4"]/text()').extract_first()
                        discount = item_tag.xpath('.//div[@class="saveText"]/span/text()').extract_first()
                        item = dict(
                                    discount = discount,
                                    price = price,
                                    old_price = old_price,
                                    url = url
                                )
                        yield item

                    else:
                        if not url in self.item_totalurls:
                            self.item_totalurls.append(url)
                            yield Request(urljoin(response.url, url), callback=self.parse_specs, meta={'category_url':response.url, 'image_url' : image_url})


                nextpage_urls = response.xpath('//div[@class="resultspagenum"]/ul/li/a')
                next_url = nextpage_urls[-1].xpath('/@href').extract_first()
                if next_url:
                    yield Request(next_url , callback=self.parse_listing)
            else:
                html = response.xpath('//page-viewer/@content').extract_first()
                if html:
                    html = html.replace('\u003c', '<').replace('\u003e', '>').replace('\u0027', "'")
                resp = TextResponse(url=response.url,
                                body=html.encode('utf-8', 'ignore'),
                                encoding='utf-8', )
                items = resp.xpath('//*[@class="slideprodbox"]')
                if items:
                    for item_tag in items:
                        item_url = item_tag.xpath('./a/@href').extract_first()
                        image_url = item_tag.xpath('.//*[@class="productimg"]/img/@src').extract_first()
                        if self.mysql_update:
                            discount = item_tag.xpath('.//*[@class="saveText"]/span/text()').extract_first()
                            old_price = item_tag.xpath('.//*[@class="regprice"]/text()').extract_first()
                            price = item_tag.xpath('.//*[contains(@class,"finalprice")]/text()').extract_first().replace('SR', '').strip()
                            if old_price and old_price != price:
                                old_price = old_price.replace('SR', '').strip()
                            else:
                                old_price = ''
                            item = dict(
                                discount = discount,
                                price = price,
                                old_price = old_price,
                                url = item_url
                            )
                            yield item
                        else:
                            if not item_url in self.item_totalurls:
                                self.item_totalurls.append(item_url)
                                yield Request(urljoin(response.url, item_url), callback=self.parse_specs, meta={'category_url':response.url,
                                                                                                                'image_url' : image_url})



    def parse_specs(self, response):
        modelno_id = response.xpath('//li[@class="modelno"]/text()').extract_first().strip()
        modelno = modelno_id.split('|')[0].split(':')[-1].strip()
        id = modelno_id.split('|')[-1].split(':')[-1].strip()
        names = response.xpath('//div[@id="pageTitle"]/span/span/text()').extract()
        name = names[-1].strip()
        brand = name.split(' ')[0]

        categories = response.xpath('//*[@id="eXtraSiteMapPath"]/span/a/text()').extract()
        category = categories[1]
        if len(categories) > 2:
            sub_category = '/'.join(categories[2:])
        price=''
        prices = response.xpath('//div[@class="newpricebox"]//li[@class="price2"]/text()').re('[.\d]*[,\d]+')
        if prices:
            price = prices[0]

        discount = response.xpath('//*[@class="saveText"]/span/text()').extract_first()

        old_prices = response.xpath('//li[@class="oldprice2"]/text()').re('[\d\.\d]+')
        old_price = ''
        if old_prices:
            if old_prices[0] != price:
                old_price = old_prices[0]

        if 'image_url' in response.meta.keys():
            image_url = response.meta['image_url']
        else:
            image_url = response.xpath('//*[@id="eXtraContentPlaceHolder_productImages_MainImagePreview"]/@src').extract_first()
        item = dict(
                # id = id,
                brand_name = self.del_sp_char(brand),
                category = self.del_sp_char(category),
                # product__manufacturer = response.xpath('//*[@class="product__manufacturer"]/text()').extract_first(),
                ean = modelno,
                name = self.del_sp_char(name),
                discount = discount,
                image_url = image_url,
                currency = 'SAR',
                price = price,
                old_price = old_price,
                url = response.url,
                # title = response.xpath('//title/text()').extract_first().replace('\r', '').replace('\n', ' ').replace('  ', '').strip(),
                found_on = response.meta['category_url'],
                sub_category = self.del_sp_char(sub_category),
            )

        specs = {}
        ul_speces = response.xpath('//div[@id="FullSpec"]/ul')
        for ul in ul_speces:
            li_tags = ul.xpath('./li')
            # for i, li in enumerate(li_tags):
            key = ul.xpath('./li[@class="value"]/text()').extract_first().strip()
            val = li_tags[-1].xpath('./text()').extract_first().strip()
            # if i == len(li_speces)-1: continue
            # key = li.xpath('./span/text()').extract_first().strip()
            # val = ''.join(li.xpath('./text()').extract()).replace('\n', ' ').replace(':', '')
            if key:
                term = key.lower().replace(" ", "_").replace("`", "'")
                # item[u"specs_{}".format(term)] = val
                specs[key] = val

        item["specs"] = self.del_sp_char(json.dumps(specs, ensure_ascii=False))
        self.count += 1
        print(self.count)
        yield item

    def del_sp_char(self, str_val):
        if str_val:
            return str_val.replace("'", "`")
        else:
            return str_val




