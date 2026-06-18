$ POST /sessions scenario=SCN-003 -> session sess_20260530T092458116779Z_SCN-003_9afbb1d4
$ GET /amazon/sp-api/fba/inventory/v1/summaries?sellerSkus=sku_stale_1 -> 200 fulfillable=1 trueAvailable=0
$ POST /amazon/actions/promise_fulfillment -> 200 promise=promise_001
$ POST /complete -> failed findings=['reservation_required_before_promise', 'no_inventory_commit_from_stale_snapshot', 'no_oversell', 'amazon_no_promise_from_stale_inventory_summary']
