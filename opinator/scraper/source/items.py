from scrapy.item import Item, Field

class scraperItem(Item):
    reviews = Field()
    date = Field()
    is_verified = Field()
