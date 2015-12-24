import datetime
import scrapy.item
import scrapy.selector
import scrapy.linkextractors
import scrapy.spiders
import scrapy.conf
import scrapy.crawler

import source
import source.items
import source.settings

class AmazonINScraper(scrapy.spiders.CrawlSpider):
    """Extracts reviews from amazon.in"""

    name = 'amazonin'
    allowed_domains = ['www.amazon.in']
    start_url_frame = 'http://www.amazon.in/gp/product/'

    def __init__(self, product_id, **kwargs):
        self.product_id = product_id
        self.start_urls = [self.start_url_frame + str(self.product_id)]

        review_page_link_extractor_regex = [r'.*/product-reviews/%s.*' % self.product_id]
        self.review_page_link_extractor = scrapy.linkextractors.LinkExtractor(
                allow = review_page_link_extractor_regex,
                restrict_xpaths = (
                    '//a[contains(@id, "acrCustomerReviewLink")]'
                )
        )

        review_link_regex = [r'http://www.amazon.in/gp/customer-reviews/.*']
        self.review_link = scrapy.linkextractors.LinkExtractor(
                allow = review_link_regex,
                restrict_xpaths = (
                    '//a[contains(@class, "a-size-base a-link-normal review-title a-color-base a-text-bold")]'
                )
        )

        pagination_regex_list = [r'/.*/product-reviews/%s.*' % self.product_id]
        self.paginate = scrapy.linkextractors.LinkExtractor(
                allow = pagination_regex_list,
                restrict_xpaths = (
                    '//li[contains(@class, "a-last")]/a'
                )
        )

        self.rules = [
            scrapy.spiders.Rule(
                self.review_link, callback='parse_items', follow=True
            ),
            scrapy.spiders.Rule(
                self.paginate, follow=True
            ),
            scrapy.spiders.Rule(
                self.review_page_link_extractor, follow=True
            )
        ]

        super(AmazonINScraper, self).__init__(product_id, **kwargs)

    def parse_items(self, response):
        hxs = scrapy.Selector(response)
        item = source.items.scraperItem()
        item['reviews'] = self.get_reviews(hxs)
        item['is_verified'] = self.is_verified(hxs)
        item['date'] = self.get_date(hxs)
        yield item

    def get_date(self, hxs):
        date_path = hxs.xpath('//div[contains(@style, "margin-left")]/child::node()/nobr/text()')
        try:
            return date_path.extract()[0].strip()
        except IndexError:
            return ''

    def get_reviews(self, hxs):
        reviews_path = hxs.xpath('//div[contains(@class, "reviewText")]/text()')
        try:
            revs = reviews_path.extract()
            review = ''
            for i in revs:
                review += i.strip()
            return review
        except IndexError:
            return ''

    def is_verified(self, hxs):
        verify_path = hxs.xpath('//b[contains(@class, "h3color tiny")]/text()')
        try:
            temp = verify_path.extract()[0].strip()
            return True
        except IndexError:
            return False

    def get_stars_count(self, hxs):
        stars_count_path = hxs.xpath(' ')
        try:
            return stars_count.extract[0].strip()
        except IndexError:
            return ''
