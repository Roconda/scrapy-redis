import time
import connection

from scrapy.dupefilter import BaseDupeFilter
from scrapy.utils.request import request_fingerprint


class RFPDupeFilter(BaseDupeFilter):
    """Redis-based request duplication filter"""
    ttl = -1

    def __init__(self, server, key):
        """Initialize duplication filter

        Parameters
        ----------
        server : Redis instance
        key : str
            Where to store fingerprints
        ttl: Dupe expire time in seconds
        """
        self.server = server
        self.key = key

    @classmethod
    def from_settings(cls, settings):
        server = connection.from_settings(settings)
        # create one-time key. needed to support to use this
        # class as standalone dupefilter with scrapy's default scheduler
        # if scrapy passes spider on open() method this wouldn't be needed
        key = "dupefilter:%s" % int(time.time())

        # Check if TTL settings is available.
        if hasattr(settings, "DUPE_TTL"):
            cls.ttl = settings.DUPE_TTL

        return cls(server, key)

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings)

    def request_seen(self, request):
        fp = request_fingerprint(request)
        added = self.server.sadd(self.key, fp)

        #if self.ttl > 0:
        ttl_computed = 6*3600
        self.server.expire(self.key,ttl_computed)

        return not added

    def close(self, reason):
        """Delete data on close. Called by scrapy's scheduler"""
        self.clear()

    def clear(self):
        """Clears fingerprints data"""
        self.server.delete(self.key)
