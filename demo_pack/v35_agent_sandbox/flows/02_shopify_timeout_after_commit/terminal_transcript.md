$ POST /sessions scenario=SCN-002 -> session sess_20260530T092457286630Z_SCN-002_00153377
$ GET /tasks/next -> task_fulfill_2001 fault=timeout_after_commit
$ mutation fulfillmentCreate(request_id=shopify_req_timeout_1) -> 504 timeout_after_commit; mutation already committed
$ mutation fulfillmentCreate(request_id=shopify_req_retry_2) -> 200 id=gid://shopify/Fulfillment/ful_002
$ POST /complete -> failed findings=['idempotency_required_for_mutating_retries', 'no_duplicate_fulfillment']
