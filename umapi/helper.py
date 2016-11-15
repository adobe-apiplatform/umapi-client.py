import math
import random
import time
from error import UMAPIError, UMAPIRetryError, UMAPIRequestError

def paginate(call, org_id, max_pages=0):
    page = 0
    records = []
    while True:
        res = make_call(call, org_id, page)
        if 'groups' in res:
            res_type = 'groups'
        else:
            res_type = 'users'
        records += res[res_type]

        page += 1
        if max_pages and max_pages >= page:
            return records

        if 'lastPage' in res and res['lastPage']:
            return records

# Copy & hack retry code from aedash_connector/connector.py
def make_call(call, org_id, page):
    num_attempts = 0
    num_attempts_max = 4
    backoff_exponential_factor = 15  # seconds
    backoff_random_delay_max = 5  # seconds

    while True:
        num_attempts += 1

        if num_attempts > num_attempts_max:
            print("ACTION FAILURE NO MORE RETRIES, SKIPPING...")
            break

        try:
            res = call(org_id, page)
            return res
        except UMAPIRequestError as e:
            print("PAGINATE ERROR - %s", e.code)
            break
        except UMAPIRetryError as e:
            print("PAGINATE FAILURE -- %s - RETRYING", e.res.status_code)
            if "Retry-After" in e.res.headers:
                retry_after_date = email.utils.parsedate_tz(e.res.headers["Retry-After"])
                if retry_after_date is not None:
                    # header contains date
                    time_backoff = int(email.utils.mktime_tz(retry_after_date) - time.time())
                else:
                    # header contains delta seconds
                    time_backoff = int(e.res.headers["Retry-After"])
            else:
                # use exponential backoff with random delayh
                time_backoff = int(math.pow(2, num_attempts - 1)) * \
                               backoff_exponential_factor + \
                               random.randint(0, backoff_random_delay_max)

            print("Retrying in " + str(time_backoff) + " seconds...")
            time.sleep(time_backoff)
            continue
        except UMAPIError as e:
            print("PAGINATE ERROR -- " + e.res.status_code  + " - " + e.res.text)
            break

        if res['result'] == 'success': # and not res['notCompleted']:
            print('PAGINATE SUCCESS -- completed') #  + res['completed'])
            break
        elif res['result'] == 'success':
            print('PAGINATE PARTIAL SUCCESS') # -- %d completed, %d failed', res['completed'], res['incomplete'])
            break
        else:
            print("PAGINATE FAILURE")
            break
