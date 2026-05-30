$ POST /sessions scenario=SCN-001 -> session sess_20260530T092455537598Z_duplicate_webhook_6a3ec191
$ POST /shopify/webhooks X-Shopify-Webhook-Id=wh_paid_001 -> 202 event=wh_paid_001
$ mutation fulfillmentCreate(webhook_id=wh_paid_001) -> 200 id=gid://shopify/Fulfillment/ful_001
$ POST /shopify/webhooks duplicate X-Shopify-Webhook-Id=wh_paid_001 -> 202 duplicate delivery accepted by permissive twin
$ mutation fulfillmentCreate(replayed webhook) -> 200 id=gid://shopify/Fulfillment/ful_002
$ POST /complete -> failed findings=['no_duplicate_fulfillment', 'webhook_dedup_required']
