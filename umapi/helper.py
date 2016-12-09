from email.utils import parsedate_tz, mktime_tz
from math import pow
from random import randint
from sys import maxsize
from time import time, sleep
from error import UMAPIError, UMAPIRetryError, UMAPIRequestError

def paginate(callable, org_id, max_pages=maxsize, max_records=maxsize):
    """
    Paginate through all results of a UMAPI query
    :param callable: a query method from a UMAPI instance (callable as a function)
    :param org_id: the organization being queried
    :param max_pages: the max number of pages to collect before returning (default all)
    :param max_records: the max number of records to collect before returning (default all)
    :return: the queried records
    """
    page_count = 0
    record_count = 0
    records = []
    while page_count < max_pages and record_count < max_records:
        res = make_call(callable, org_id, page_count)
        page_count += 1
        # the following incredibly ugly piece of code is very fragile.
        # the problem is that we are a "dumb helper" that doesn't understand
        # the semantics of the UMAPI or know which callable we were given.
        # TODO: make this better, probably by being smart about the callable
        if "groups" in res:
            records += res["groups"]
        elif "users" in res:
            records += res["users"]
        record_count = len(records)
        if res.get("lastPage"):
            break
    return records


def make_call(callable, org_id, page):
    """
    Make a single UMAPI call with error handling and server-controlled throttling.
    (Adapted from sample code at https://www.adobe.io/products/usermanagement/docs/samples#retry)
    :param callable: a query method from a UMAPI instance (callable as a function)
    :param org_id: the organization being queried
    :param page: the page number of the desired result set
    :return: the json (dictionary) received from the server (if any)
    """
    wait_time = 0
    num_attempts = 0
    num_attempts_max = 4
    backoff_exponential_factor = 15  # seconds
    backoff_random_delay_max = 5  # seconds

    while num_attempts < num_attempts_max:
        if wait_time > 0:
            sleep(wait_time)
            wait_time = 0
        try:
            num_attempts += 1
            return callable(org_id, page)
        except UMAPIRetryError as e:
            print("UMAPI service temporarily unavailable (attempt %d) -- %s", num_attempts, e.res.status_code)
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
                delay = randint(0, backoff_random_delay_max)
                wait_time = (int(pow(2, num_attempts)) * backoff_exponential_factor) + delay
            print("Next retry in %d seconds...", wait_time)
            continue
        except UMAPIRequestError as e:
            print("UMAPI error processing request -- %s", e.code)
            return {}
        except UMAPIError as e:
            print("HTTP error processing request -- %s: %s", e.res.status_code, e.res.text)
            return {}
    print("UMAPI timeout...giving up on results page %d after %d attempts.", page, num_attempts_max)
    return {}
