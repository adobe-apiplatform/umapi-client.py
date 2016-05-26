def paginate(call, org_id, max_pages=0):
    page = 0
    records = []
    while True:
        res = call(org_id, page)
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
