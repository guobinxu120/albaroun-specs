# -*- coding: utf-8 -*-
import scrapy
import json

class SouqSpider(scrapy.Spider):
    name = 'souq'
    allowed_domains = ['souq.com']
    start_urls = ['https://saudi.souq.com/sa-en/shop-all-categories/c/']
    listing_page = None #"https://saudi.souq.com/sa-en/tote/handbags-472/a-t/s/"

    def parse(self, response):
        if self.listing_page:
            yield response.follow(self.listing_page, callback=self.parse_listing)
        else:
            urls = response.css(".shop-all-container a::attr(href)").extract()
            for url in urls:
                if url:
                    yield response.follow(url, callback=self.parse_listing)

    def parse_listing(self, response):
        items = response.xpath('//div[@class="category-products"]/ul/li/a/@href').extract()
        for item in items:
            image_url = item.css(".img-bucket img.img-size-medium::attr(data-src)").extract_first()
            if not image_url:
                image_url = item.css(".img-bucket img::attr(src)").extract_first()

            url = item.css(".itemLink::attr(href)").extract_first()

            item = dict(
                id = item.css(".quickViewAction::attr(data-id)").extract_first(),
                brand_name = item.xpath("@data-brand-name").extract_first(),
                category = item.xpath("@data-category-name").extract_first(),
                id_winner_unit = item.xpath("@data-id-winner-unit").extract_first(),
                ean = item.xpath("@data-ean").extract_first(),
                name = item.xpath("@data-name").extract_first(),
                discount = item.css(".discount::text").extract_first(),
                image_url = image_url,
                currency = item.css(".currency-text::text").extract_first(),
                price = item.css(".itemPrice::text").extract_first(),
                old_price = item.css(".itemOldPrice::text").extract_first(),
                url = url,
                title = item.css(".title::text").extract_first(),
                found_on = response.url,
            )
            yield response.follow(
                item,
                callback=self.parse_specs
            )

        next_page = response.css(".pagination-next a::attr(href)").extract_first()
        if next_page:
            yield response.follow(next_page, callback=self.parse_listing)
    def parse_specs(self, response):
        item = response.meta.get("item")
        specs = {}
        for dt in response.css("#specs-full dt"):
            dd = dt.xpath("following-sibling::dd[1]")
            term = dt.xpath("text()").extract_first()
            definition = dd.xpath("text()").extract_first()
            if dd.css("i.fi-x"):
                definition = "n"
            elif dd.css("i.fi-check"):
                definition = "y"
            if term:
                term = term.lower().replace(" ", "_").replace("`", "'")
                item[u"specs_{}".format(term)] = definition
                specs[term] = definition

        item["specs"] = json.dumps(specs)
        yield item
            
            




