$ POST /sessions scenario=SCN-005 -> session sess_20260530T092459654606Z_SCN-005_ce085f0c
$ POST /amazon/notifications ORDER_CHANGE BuyerRequestedCancel -> 202 event=cancel_request
$ POST /amazon/actions/cancel_order -> 200 ok=True
$ POST /amazon/sp-api/orders/v0/orders/AMZ-5001/shipmentConfirmation -> 200 shipmentStatus=confirmed
$ POST /complete -> failed findings=['warehouse_conflict_requires_hold', 'no_ship_after_cancel', 'amazon_no_confirm_shipment_after_buyer_cancel_without_review']
