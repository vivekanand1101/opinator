from scrapy.exceptions import DropItem

class scraperPipeline(object):
    def process_item (self, item, spider):
        if item['is_verified'] == False:
            raise DropItem('Not a verified review')
        return item
