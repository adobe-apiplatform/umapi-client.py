# Copyright (c) 2016 Adobe Systems Incorporated.  All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
from email.utils import parsedate_tz, mktime_tz
from math import pow
from random import randint
from sys import maxsize
from time import time, sleep
from .error import UMAPIError, UMAPIRetryError, UMAPIRequestError

# make the retry options module-global so they can be set by clients
retry_max_attempts = 4
retry_exponential_backoff_factor = 15  # seconds
retry_random_delay_max = 5  # seconds

# make the logger module-global so it can be set by clients
logger = logging.getLogger(__name__)


def paginate(query, org_id, max_pages=maxsize, max_records=maxsize):
    """
    Paginate through all results of a UMAPI query
    :param query: a query method from a UMAPI instance (callable as a function)
    :param org_id: the organization being queried
    :param max_pages: the max number of pages to collect before returning (default all)
    :param max_records: the max number of records to collect before returning (default all)
    :return: the queried records
    """
    page_count = 0
    record_count = 0
    records = []
    while page_count < max_pages and record_count < max_records:
        res = make_call(query, org_id, page_count)
        page_count += 1
        # the following incredibly ugly piece of code is very fragile.
        # the problem is that we are a "dumb helper" that doesn't understand
        # the semantics of the UMAPI or know which query we were given.
        # TODO: make this better, probably by being smart about the query
        if "groups" in res:
            records += res["groups"]
        elif "users" in res:
            records += res["users"]
        record_count = len(records)
        if res.get("lastPage"):
            break
    return records


def make_call(query, org_id, page):
    """
    Make a single UMAPI call with error handling and server-controlled throttling.
    (Adapted from sample code at https://www.adobe.io/products/usermanagement/docs/samples#retry)
    :param query: a query method from a UMAPI instance (callable as a function)
    :param org_id: the organization being queried
    :param page: the page number of the desired result set
    :return: the json (dictionary) received from the server (if any)
    """
    wait_time = 0
    num_attempts = 0

    while num_attempts < retry_max_attempts:
        if wait_time > 0:
            sleep(wait_time)
            wait_time = 0
        try:
            num_attempts += 1
            return query(org_id, page)
        except UMAPIRetryError as e:
            logger.warning("UMAPI service temporarily unavailable (attempt %d) -- %s", num_attempts, e.res.status_code)
            if "Retry-After" in e.res.headers:
                advice = e.res.headers["Retry-After"]
                advised_time = parsedate_tz(advice)
                if advised_time is not None:
                    # header contains date
                    wait_time = int(mktime_tz(advised_time) - time())
                else:
                    # header contains delta seconds
                    wait_time = int(advice)
            if wait_time <= 0:
                # use exponential back-off with random delay
                delay = randint(0, retry_random_delay_max)
                wait_time = (int(pow(2, num_attempts)) * retry_exponential_backoff_factor) + delay
            logger.warning("Next retry in %d seconds...", wait_time)
            continue
        except UMAPIRequestError as e:
            logger.warning("UMAPI error processing request -- %s", e.code)
            return {}
        except UMAPIError as e:
            logger.warning("HTTP error processing request -- %s: %s", e.res.status_code, e.res.text)
            return {}
    logger.error("UMAPI timeout...giving up on results page %d after %d attempts.", page, retry_max_attempts)
    return {}
