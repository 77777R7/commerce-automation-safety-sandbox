window.DEMO_VIEWER_DATA = {
  "generatedAt": "static-demo-viewer",
  "summary": {
    "scenarioCount": 5,
    "badFailures": 5,
    "goodPasses": 5,
    "totalFindings": 12
  },
  "offlineAudit": {
    "title": "Offline Fulfillment Automation Audit",
    "riskScore": "100/100",
    "cleanScore": "0/100",
    "findings": [
      "offline_duplicate_fulfillment",
      "offline_negative_available_inventory",
      "offline_paid_order_inventory_shortage",
      "offline_cancel_after_pick_pack_conflict",
      "offline_refund_after_shipment_without_approval"
    ],
    "ask": "Send four exports: orders, inventory, fulfillments, refunds. No API keys, no live store access."
  },
  "scenarios": [
    {
      "id": "SCN-001",
      "slug": "SCN-001_duplicate_webhook_fulfillment",
      "title": "Duplicate Webhook Fulfillment",
      "accident": "同一个 paid order webhook 被重复处理。",
      "businessLoss": "重复发货、重复扣库存、重复仓库通知和客服追损。",
      "badBehavior": "坏流程没有记录 webhook delivery ID，第二次收到同一事件时又预留库存并创建履约。",
      "goodBehavior": "好流程先做 webhook dedupe，第二次收到同一 delivery 直接跳过。",
      "fix": "把 webhook ID / delivery ID 存为幂等键；任何改变订单、库存、履约状态的动作前先检查是否已处理。",
      "gate": "上线前重放 duplicate webhook；只要产生重复 fulfillment 或重复 reservation，就阻止发布。",
      "risk": "no_duplicate_fulfillment",
      "impact": "The automation created more fulfillment than the order requires, creating duplicate shipment and inventory loss risk.",
      "recommendation": "Check existing fulfillment state before creating another fulfillment, and use a stable dedupe or idempotency key for repeated delivery or retry paths.",
      "bad": {
        "status": "failed",
        "runId": "run_20260529T063812178261Z_duplicate_webhook_bad_runner",
        "findings": [
          {
            "policy_id": "no_duplicate_fulfillment",
            "severity": "critical",
            "status": "failed",
            "evidence": {
              "order_id": "order_1001",
              "sku": "sku_widget_1",
              "ordered_quantity": 1,
              "fulfilled_quantity": 2,
              "fulfillment_count": 2,
              "fulfillment_ids": [
                "ful_001",
                "ful_002"
              ],
              "webhook_ids": [
                "wh_paid_001",
                "wh_paid_001"
              ],
              "source_event_ids": [
                "wh_paid_001",
                "wh_paid_001"
              ],
              "idempotency_keys": [
                null,
                null
              ]
            },
            "business_impact": "The automation created more fulfillment than the order requires, creating duplicate shipment and inventory loss risk.",
            "recommendation": "Check existing fulfillment state before creating another fulfillment, and use a stable dedupe or idempotency key for repeated delivery or retry paths."
          },
          {
            "policy_id": "webhook_dedup_required",
            "severity": "critical",
            "status": "failed",
            "evidence": {
              "webhook_id": "wh_paid_001",
              "times_received": 2,
              "side_effect_count": 4,
              "side_effects_from_same_webhook": [
                {
                  "type": "reservation",
                  "id": "res_001",
                  "order_id": "order_1001",
                  "sku": "sku_widget_1",
                  "quantity": 1
                },
                {
                  "type": "reservation",
                  "id": "res_002",
                  "order_id": "order_1001",
                  "sku": "sku_widget_1",
                  "quantity": 1
                },
                {
                  "type": "fulfillment",
                  "id": "ful_001",
                  "order_id": "order_1001",
                  "sku": "sku_widget_1",
                  "quantity": 1
                },
                {
                  "type": "fulfillment",
                  "id": "ful_002",
                  "order_id": "order_1001",
                  "sku": "sku_widget_1",
                  "quantity": 1
                }
              ],
              "dedupe_signal": "missing"
            },
            "business_impact": "The duplicate webhook was processed as a new business event, so retries from the platform can trigger repeated state-changing work such as inventory reservation, refunds, or fulfillment.",
            "recommendation": "Store processed webhook IDs and skip repeat deliveries before performing mutating actions."
          }
        ],
        "timeline": [
          {
            "step": 1,
            "actor": "scenario",
            "event": "webhook_received",
            "message": "Webhook wh_paid_001 received for order order_1001.",
            "details": {
              "type": "webhook",
              "id": "wh_paid_001",
              "topic": "order_paid",
              "order_id": "order_1001"
            }
          },
          {
            "step": 2,
            "actor": "bad_runner",
            "event": "webhook_processing_started",
            "message": "bad_runner starts processing webhook wh_paid_001 without dedupe.",
            "details": {
              "webhook_id": "wh_paid_001",
              "order_id": "order_1001"
            }
          },
          {
            "step": 3,
            "actor": "bad_runner",
            "event": "inventory_reserved",
            "message": "bad_runner reserves 1 unit(s) of sku_widget_1; reserved inventory is now 1.",
            "details": {
              "reservation_id": "res_001",
              "order_id": "order_1001",
              "sku": "sku_widget_1",
              "quantity": 1,
              "created_by": "bad_runner",
              "webhook_id": "wh_paid_001"
            }
          },
          {
            "step": 4,
            "actor": "bad_runner",
            "event": "fulfillment_created",
            "message": "bad_runner creates fulfillment ful_001 for order order_1001, sku sku_widget_1.",
            "details": {
              "fulfillment_id": "ful_001",
              "order_id": "order_1001",
              "sku": "sku_widget_1",
              "quantity": 1,
              "created_by": "bad_runner",
              "webhook_id": "wh_paid_001",
              "idempotency_key": null,
              "request_id": null,
              "source_event_id": "wh_paid_001"
            }
          },
          {
            "step": 5,
            "actor": "scenario",
            "event": "webhook_received",
            "message": "Webhook wh_paid_001 received for order order_1001.",
            "details": {
              "type": "webhook",
              "id": "wh_paid_001",
              "topic": "order_paid",
              "order_id": "order_1001"
            }
          },
          {
            "step": 6,
            "actor": "bad_runner",
            "event": "webhook_processing_started",
            "message": "bad_runner starts processing webhook wh_paid_001 without dedupe.",
            "details": {
              "webhook_id": "wh_paid_001",
              "order_id": "order_1001"
            }
          },
          {
            "step": 7,
            "actor": "bad_runner",
            "event": "inventory_reserved",
            "message": "bad_runner reserves 1 unit(s) of sku_widget_1; reserved inventory is now 2.",
            "details": {
              "reservation_id": "res_002",
              "order_id": "order_1001",
              "sku": "sku_widget_1",
              "quantity": 1,
              "created_by": "bad_runner",
              "webhook_id": "wh_paid_001"
            }
          },
          {
            "step": 8,
            "actor": "bad_runner",
            "event": "fulfillment_created",
            "message": "bad_runner creates fulfillment ful_002 for order order_1001, sku sku_widget_1.",
            "details": {
              "fulfillment_id": "ful_002",
              "order_id": "order_1001",
              "sku": "sku_widget_1",
              "quantity": 1,
              "created_by": "bad_runner",
              "webhook_id": "wh_paid_001",
              "idempotency_key": null,
              "request_id": null,
              "source_event_id": "wh_paid_001"
            }
          },
          {
            "step": 9,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: no_duplicate_fulfillment (critical).",
            "details": {
              "policy_id": "no_duplicate_fulfillment",
              "severity": "critical",
              "status": "failed",
              "evidence": {
                "order_id": "order_1001",
                "sku": "sku_widget_1",
                "ordered_quantity": 1,
                "fulfilled_quantity": 2,
                "fulfillment_count": 2,
                "fulfillment_ids": [
                  "ful_001",
                  "ful_002"
                ],
                "webhook_ids": [
                  "wh_paid_001",
                  "wh_paid_001"
                ],
                "source_event_ids": [
                  "wh_paid_001",
                  "wh_paid_001"
                ],
                "idempotency_keys": [
                  null,
                  null
                ]
              },
              "business_impact": "The automation created more fulfillment than the order requires, creating duplicate shipment and inventory loss risk.",
              "recommendation": "Check existing fulfillment state before creating another fulfillment, and use a stable dedupe or idempotency key for repeated delivery or retry paths."
            }
          },
          {
            "step": 10,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: webhook_dedup_required (critical).",
            "details": {
              "policy_id": "webhook_dedup_required",
              "severity": "critical",
              "status": "failed",
              "evidence": {
                "webhook_id": "wh_paid_001",
                "times_received": 2,
                "side_effect_count": 4,
                "side_effects_from_same_webhook": [
                  {
                    "type": "reservation",
                    "id": "res_001",
                    "order_id": "order_1001",
                    "sku": "sku_widget_1",
                    "quantity": 1
                  },
                  {
                    "type": "reservation",
                    "id": "res_002",
                    "order_id": "order_1001",
                    "sku": "sku_widget_1",
                    "quantity": 1
                  },
                  {
                    "type": "fulfillment",
                    "id": "ful_001",
                    "order_id": "order_1001",
                    "sku": "sku_widget_1",
                    "quantity": 1
                  },
                  {
                    "type": "fulfillment",
                    "id": "ful_002",
                    "order_id": "order_1001",
                    "sku": "sku_widget_1",
                    "quantity": 1
                  }
                ],
                "dedupe_signal": "missing"
              },
              "business_impact": "The duplicate webhook was processed as a new business event, so retries from the platform can trigger repeated state-changing work such as inventory reservation, refunds, or fulfillment.",
              "recommendation": "Store processed webhook IDs and skip repeat deliveries before performing mutating actions."
            }
          }
        ],
        "signals": {
          "duplicate_fulfillment": true,
          "duplicated_reserved_inventory": true,
          "excess_reserved_inventory": {
            "sku_widget_1": 1
          }
        },
        "counts": {
          "fulfillments": {
            "before": 0,
            "after": 2
          },
          "promises": {
            "before": 0,
            "after": 0
          },
          "refunds": {
            "before": 0,
            "after": 0
          },
          "approvalRequests": {
            "before": 0,
            "after": 0
          },
          "inventoryReleases": {
            "before": 0,
            "after": 0
          },
          "workflowHolds": {
            "before": 0,
            "after": 0
          },
          "warehouseCancellationRequests": {
            "before": 0,
            "after": 0
          }
        }
      },
      "good": {
        "status": "passed",
        "runId": "run_20260529T063812188720Z_duplicate_webhook_good_runner",
        "findings": [],
        "timeline": [
          {
            "step": 1,
            "actor": "scenario",
            "event": "webhook_received",
            "message": "Webhook wh_paid_001 received for order order_1001.",
            "details": {
              "type": "webhook",
              "id": "wh_paid_001",
              "topic": "order_paid",
              "order_id": "order_1001"
            }
          },
          {
            "step": 2,
            "actor": "good_runner",
            "event": "webhook_processing_started",
            "message": "good_runner starts processing webhook wh_paid_001 with dedupe.",
            "details": {
              "webhook_id": "wh_paid_001",
              "order_id": "order_1001"
            }
          },
          {
            "step": 3,
            "actor": "good_runner",
            "event": "inventory_reserved",
            "message": "good_runner reserves 1 unit(s) of sku_widget_1; reserved inventory is now 1.",
            "details": {
              "reservation_id": "res_001",
              "order_id": "order_1001",
              "sku": "sku_widget_1",
              "quantity": 1,
              "created_by": "good_runner",
              "webhook_id": "wh_paid_001"
            }
          },
          {
            "step": 4,
            "actor": "good_runner",
            "event": "fulfillment_created",
            "message": "good_runner creates fulfillment ful_001 for order order_1001, sku sku_widget_1.",
            "details": {
              "fulfillment_id": "ful_001",
              "order_id": "order_1001",
              "sku": "sku_widget_1",
              "quantity": 1,
              "created_by": "good_runner",
              "webhook_id": "wh_paid_001",
              "idempotency_key": "fulfillment:order_1001:sku_widget_1",
              "request_id": null,
              "source_event_id": "wh_paid_001"
            }
          },
          {
            "step": 5,
            "actor": "scenario",
            "event": "webhook_received",
            "message": "Webhook wh_paid_001 received for order order_1001.",
            "details": {
              "type": "webhook",
              "id": "wh_paid_001",
              "topic": "order_paid",
              "order_id": "order_1001"
            }
          },
          {
            "step": 6,
            "actor": "good_runner",
            "event": "duplicate_webhook_skipped",
            "message": "good_runner skips duplicate webhook wh_paid_001.",
            "details": {
              "type": "webhook",
              "id": "wh_paid_001",
              "topic": "order_paid",
              "order_id": "order_1001"
            }
          },
          {
            "step": 7,
            "actor": "policy_engine",
            "event": "policy_check_passed",
            "message": "Policy check passed with no violations.",
            "details": {
              "status": "passed"
            }
          }
        ],
        "signals": {},
        "counts": {
          "fulfillments": {
            "before": 0,
            "after": 1
          },
          "promises": {
            "before": 0,
            "after": 0
          },
          "refunds": {
            "before": 0,
            "after": 0
          },
          "approvalRequests": {
            "before": 0,
            "after": 0
          },
          "inventoryReleases": {
            "before": 0,
            "after": 0
          },
          "workflowHolds": {
            "before": 0,
            "after": 0
          },
          "warehouseCancellationRequests": {
            "before": 0,
            "after": 0
          }
        }
      }
    },
    {
      "id": "SCN-002",
      "slug": "SCN-002_timeout_after_commit_retry",
      "title": "Timeout After Commit Unsafe Retry",
      "accident": "第一次履约已经提交成功，但客户端收到 timeout 后盲目重试。",
      "businessLoss": "重复 fulfillment、重复出库、额外运费和库存损失。",
      "badBehavior": "坏流程没有稳定 idempotency_key，timeout 后直接创建第二个 fulfillment。",
      "goodBehavior": "好流程使用稳定 idempotency_key，并在 timeout 后查询已提交的 fulfillment。",
      "fix": "所有 mutating retry 都使用稳定幂等键；timeout 后先查询当前状态，再决定是否重试。",
      "gate": "上线前注入 timeout_after_commit；只要 retry 造成第二个副作用，就阻止发布。",
      "risk": "idempotency_required_for_mutating_retries",
      "impact": "The first fulfillment committed, but the automation received a timeout and retried as a new mutation. This can create duplicate fulfillment when the system was actually successful.",
      "recommendation": "Use a stable idempotency key for mutating fulfillment requests and, after timeout, query existing fulfillment state before retrying.",
      "bad": {
        "status": "failed",
        "runId": "run_20260529T063815329071Z_SCN-002_bad_runner",
        "findings": [
          {
            "policy_id": "idempotency_required_for_mutating_retries",
            "severity": "critical",
            "status": "failed",
            "evidence": {
              "source_event_id": "task_fulfill_2001",
              "fault": "timeout_after_commit",
              "action": "create_fulfillment",
              "order_id": "order_2001",
              "sku": "sku_retry_1",
              "fulfillment_ids": [
                "ful_001",
                "ful_002"
              ],
              "request_ids": [
                "task_fulfill_2001:attempt_1",
                "task_fulfill_2001:attempt_2"
              ],
              "idempotency_keys": [
                null,
                null
              ],
              "missing_idempotency_key": true
            },
            "business_impact": "The first fulfillment committed, but the automation received a timeout and retried as a new mutation. This can create duplicate fulfillment when the system was actually successful.",
            "recommendation": "Use a stable idempotency key for mutating fulfillment requests and, after timeout, query existing fulfillment state before retrying."
          },
          {
            "policy_id": "no_duplicate_fulfillment",
            "severity": "critical",
            "status": "failed",
            "evidence": {
              "order_id": "order_2001",
              "sku": "sku_retry_1",
              "ordered_quantity": 1,
              "fulfilled_quantity": 2,
              "fulfillment_count": 2,
              "fulfillment_ids": [
                "ful_001",
                "ful_002"
              ],
              "webhook_ids": [
                null,
                null
              ],
              "source_event_ids": [
                "task_fulfill_2001",
                "task_fulfill_2001"
              ],
              "idempotency_keys": [
                null,
                null
              ]
            },
            "business_impact": "The automation created more fulfillment than the order requires, creating duplicate shipment and inventory loss risk.",
            "recommendation": "Check existing fulfillment state before creating another fulfillment, and use a stable dedupe or idempotency key for repeated delivery or retry paths."
          }
        ],
        "timeline": [
          {
            "step": 1,
            "actor": "scenario",
            "event": "fulfillment_task_received",
            "message": "Fulfillment task task_fulfill_2001 received for order order_2001 with fault timeout_after_commit.",
            "details": {
              "type": "fulfillment_task",
              "id": "task_fulfill_2001",
              "order_id": "order_2001",
              "fault": {
                "type": "timeout_after_commit",
                "action": "create_fulfillment"
              }
            }
          },
          {
            "step": 2,
            "actor": "bad_runner",
            "event": "fulfillment_task_processing_started",
            "message": "bad_runner starts task task_fulfill_2001 without an idempotency key.",
            "details": {
              "task_id": "task_fulfill_2001",
              "order_id": "order_2001"
            }
          },
          {
            "step": 3,
            "actor": "bad_runner",
            "event": "fulfillment_created",
            "message": "bad_runner creates fulfillment ful_001 for order order_2001, sku sku_retry_1.",
            "details": {
              "fulfillment_id": "ful_001",
              "order_id": "order_2001",
              "sku": "sku_retry_1",
              "quantity": 1,
              "created_by": "bad_runner",
              "webhook_id": null,
              "idempotency_key": null,
              "request_id": "task_fulfill_2001:attempt_1",
              "source_event_id": "task_fulfill_2001"
            }
          },
          {
            "step": 4,
            "actor": "commerce_twin",
            "event": "fault_injected",
            "message": "Twin committed fulfillment ful_001, then returned timeout_after_commit.",
            "details": {
              "type": "timeout_after_commit",
              "action": "create_fulfillment",
              "fulfillment_id": "ful_001",
              "order_id": "order_2001",
              "sku": "sku_retry_1",
              "idempotency_key": null,
              "request_id": "task_fulfill_2001:attempt_1",
              "source_event_id": "task_fulfill_2001"
            }
          },
          {
            "step": 5,
            "actor": "bad_runner",
            "event": "timeout_received",
            "message": "bad_runner receives timeout_after_commit and assumes the fulfillment failed.",
            "details": {
              "task_id": "task_fulfill_2001",
              "retry_strategy": "blind_retry"
            }
          },
          {
            "step": 6,
            "actor": "bad_runner",
            "event": "fulfillment_created",
            "message": "bad_runner creates fulfillment ful_002 for order order_2001, sku sku_retry_1.",
            "details": {
              "fulfillment_id": "ful_002",
              "order_id": "order_2001",
              "sku": "sku_retry_1",
              "quantity": 1,
              "created_by": "bad_runner",
              "webhook_id": null,
              "idempotency_key": null,
              "request_id": "task_fulfill_2001:attempt_2",
              "source_event_id": "task_fulfill_2001"
            }
          },
          {
            "step": 7,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: idempotency_required_for_mutating_retries (critical).",
            "details": {
              "policy_id": "idempotency_required_for_mutating_retries",
              "severity": "critical",
              "status": "failed",
              "evidence": {
                "source_event_id": "task_fulfill_2001",
                "fault": "timeout_after_commit",
                "action": "create_fulfillment",
                "order_id": "order_2001",
                "sku": "sku_retry_1",
                "fulfillment_ids": [
                  "ful_001",
                  "ful_002"
                ],
                "request_ids": [
                  "task_fulfill_2001:attempt_1",
                  "task_fulfill_2001:attempt_2"
                ],
                "idempotency_keys": [
                  null,
                  null
                ],
                "missing_idempotency_key": true
              },
              "business_impact": "The first fulfillment committed, but the automation received a timeout and retried as a new mutation. This can create duplicate fulfillment when the system was actually successful.",
              "recommendation": "Use a stable idempotency key for mutating fulfillment requests and, after timeout, query existing fulfillment state before retrying."
            }
          },
          {
            "step": 8,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: no_duplicate_fulfillment (critical).",
            "details": {
              "policy_id": "no_duplicate_fulfillment",
              "severity": "critical",
              "status": "failed",
              "evidence": {
                "order_id": "order_2001",
                "sku": "sku_retry_1",
                "ordered_quantity": 1,
                "fulfilled_quantity": 2,
                "fulfillment_count": 2,
                "fulfillment_ids": [
                  "ful_001",
                  "ful_002"
                ],
                "webhook_ids": [
                  null,
                  null
                ],
                "source_event_ids": [
                  "task_fulfill_2001",
                  "task_fulfill_2001"
                ],
                "idempotency_keys": [
                  null,
                  null
                ]
              },
              "business_impact": "The automation created more fulfillment than the order requires, creating duplicate shipment and inventory loss risk.",
              "recommendation": "Check existing fulfillment state before creating another fulfillment, and use a stable dedupe or idempotency key for repeated delivery or retry paths."
            }
          }
        ],
        "signals": {
          "duplicate_fulfillment": true
        },
        "counts": {
          "fulfillments": {
            "before": 0,
            "after": 2
          },
          "promises": {
            "before": 0,
            "after": 0
          },
          "refunds": {
            "before": 0,
            "after": 0
          },
          "approvalRequests": {
            "before": 0,
            "after": 0
          },
          "inventoryReleases": {
            "before": 0,
            "after": 0
          },
          "workflowHolds": {
            "before": 0,
            "after": 0
          },
          "warehouseCancellationRequests": {
            "before": 0,
            "after": 0
          }
        }
      },
      "good": {
        "status": "passed",
        "runId": "run_20260529T063815342075Z_SCN-002_good_runner",
        "findings": [],
        "timeline": [
          {
            "step": 1,
            "actor": "scenario",
            "event": "fulfillment_task_received",
            "message": "Fulfillment task task_fulfill_2001 received for order order_2001 with fault timeout_after_commit.",
            "details": {
              "type": "fulfillment_task",
              "id": "task_fulfill_2001",
              "order_id": "order_2001",
              "fault": {
                "type": "timeout_after_commit",
                "action": "create_fulfillment"
              }
            }
          },
          {
            "step": 2,
            "actor": "good_runner",
            "event": "fulfillment_task_processing_started",
            "message": "good_runner starts task task_fulfill_2001 with stable idempotency key.",
            "details": {
              "task_id": "task_fulfill_2001",
              "order_id": "order_2001",
              "idempotency_key": "fulfillment:order_2001:sku_retry_1:create"
            }
          },
          {
            "step": 3,
            "actor": "good_runner",
            "event": "fulfillment_created",
            "message": "good_runner creates fulfillment ful_001 for order order_2001, sku sku_retry_1.",
            "details": {
              "fulfillment_id": "ful_001",
              "order_id": "order_2001",
              "sku": "sku_retry_1",
              "quantity": 1,
              "created_by": "good_runner",
              "webhook_id": null,
              "idempotency_key": "fulfillment:order_2001:sku_retry_1:create",
              "request_id": "task_fulfill_2001:attempt_1",
              "source_event_id": "task_fulfill_2001"
            }
          },
          {
            "step": 4,
            "actor": "commerce_twin",
            "event": "fault_injected",
            "message": "Twin committed fulfillment ful_001, then returned timeout_after_commit.",
            "details": {
              "type": "timeout_after_commit",
              "action": "create_fulfillment",
              "fulfillment_id": "ful_001",
              "order_id": "order_2001",
              "sku": "sku_retry_1",
              "idempotency_key": "fulfillment:order_2001:sku_retry_1:create",
              "request_id": "task_fulfill_2001:attempt_1",
              "source_event_id": "task_fulfill_2001"
            }
          },
          {
            "step": 5,
            "actor": "good_runner",
            "event": "timeout_received",
            "message": "good_runner receives timeout_after_commit and checks existing fulfillment state before retrying.",
            "details": {
              "task_id": "task_fulfill_2001",
              "retry_strategy": "query_before_retry"
            }
          },
          {
            "step": 6,
            "actor": "good_runner",
            "event": "existing_fulfillment_confirmed",
            "message": "good_runner confirms fulfillment ful_001 already committed.",
            "details": {
              "task_id": "task_fulfill_2001",
              "fulfillment_id": "ful_001",
              "idempotency_key": "fulfillment:order_2001:sku_retry_1:create"
            }
          },
          {
            "step": 7,
            "actor": "policy_engine",
            "event": "policy_check_passed",
            "message": "Policy check passed with no violations.",
            "details": {
              "status": "passed"
            }
          }
        ],
        "signals": {},
        "counts": {
          "fulfillments": {
            "before": 0,
            "after": 1
          },
          "promises": {
            "before": 0,
            "after": 0
          },
          "refunds": {
            "before": 0,
            "after": 0
          },
          "approvalRequests": {
            "before": 0,
            "after": 0
          },
          "inventoryReleases": {
            "before": 0,
            "after": 0
          },
          "workflowHolds": {
            "before": 0,
            "after": 0
          },
          "warehouseCancellationRequests": {
            "before": 0,
            "after": 0
          }
        }
      }
    },
    {
      "id": "SCN-003",
      "slug": "SCN-003_stale_inventory_oversell",
      "title": "Stale Inventory Oversell",
      "accident": "自动化相信过期库存快照，在真实可售为 0 时仍承诺发货。",
      "businessLoss": "超卖、取消订单、差评、补偿和客服工单。",
      "badBehavior": "坏流程读取 local available=1，没有刷新库存，也没有先做 reservation。",
      "goodBehavior": "好流程刷新库存，发现 true available=0 后转人工 review。",
      "fix": "承诺发货前必须用新鲜库存做 reservation；库存不新鲜或 reserve 失败时进入人工处理。",
      "gate": "上线前注入 stale inventory；只要流程基于 stale snapshot 做承诺，就阻止发布。",
      "risk": "reservation_required_before_promise",
      "impact": "The automation promised fulfillment without reserving inventory for this order. If the visible stock was stale, the seller can oversell and later cancel or disappoint the customer.",
      "recommendation": "Reserve inventory for the order before promising fulfillment. If fresh inventory cannot be reserved, route the order to manual review.",
      "bad": {
        "status": "failed",
        "runId": "run_20260529T063818043907Z_SCN-003_bad_runner",
        "findings": [
          {
            "policy_id": "reservation_required_before_promise",
            "severity": "critical",
            "status": "failed",
            "evidence": {
              "promise_id": "promise_001",
              "order_id": "order_3001",
              "sku": "sku_stale_1",
              "quantity": 1,
              "based_on_available": 1,
              "true_available_at_commit": 0,
              "reservation_id": null,
              "matching_reservations": []
            },
            "business_impact": "The automation promised fulfillment without reserving inventory for this order. If the visible stock was stale, the seller can oversell and later cancel or disappoint the customer.",
            "recommendation": "Reserve inventory for the order before promising fulfillment. If fresh inventory cannot be reserved, route the order to manual review."
          },
          {
            "policy_id": "no_inventory_commit_from_stale_snapshot",
            "severity": "high",
            "status": "failed",
            "evidence": {
              "promise_id": "promise_001",
              "order_id": "order_3001",
              "sku": "sku_stale_1",
              "quantity": 1,
              "based_on_available": 1,
              "true_available_at_commit": 0,
              "stale_markers": {
                "last_synced_at": "stale",
                "snapshot_version": "stale"
              }
            },
            "business_impact": "The automation committed a fulfillment promise from an outdated inventory snapshot. Stale stock data can turn a normal order into an oversell incident.",
            "recommendation": "Refresh inventory before committing customer-facing promises, and block or review the action when the inventory snapshot is stale."
          },
          {
            "policy_id": "no_oversell",
            "severity": "critical",
            "status": "failed",
            "evidence": {
              "promise_id": "promise_001",
              "order_id": "order_3001",
              "sku": "sku_stale_1",
              "promised_quantity": 1,
              "true_available_at_commit": 0,
              "oversell_quantity": 1
            },
            "business_impact": "The automation promised more units than were truly available, creating cancellation, backorder, extra support, and review risk.",
            "recommendation": "Only promise fulfillment after a successful reservation against fresh available inventory."
          }
        ],
        "timeline": [
          {
            "step": 1,
            "actor": "scenario",
            "event": "inventory_promise_task_received",
            "message": "Inventory promise task task_promise_3001 received for order order_3001 with fault stale_inventory_snapshot.",
            "details": {
              "type": "inventory_promise_task",
              "id": "task_promise_3001",
              "order_id": "order_3001",
              "fault": {
                "type": "stale_inventory_snapshot"
              }
            }
          },
          {
            "step": 2,
            "actor": "bad_runner",
            "event": "inventory_snapshot_read",
            "message": "bad_runner reads stale inventory for sku_stale_1: available=1, true_available=0.",
            "details": {
              "task_id": "task_promise_3001",
              "sku": "sku_stale_1",
              "available": 1,
              "true_available": 0,
              "last_synced_at": "stale"
            }
          },
          {
            "step": 3,
            "actor": "bad_runner",
            "event": "fulfillment_promised",
            "message": "bad_runner promises fulfillment for order order_3001, sku sku_stale_1, using available=1 without confirmed reservation.",
            "details": {
              "promise_id": "promise_001",
              "order_id": "order_3001",
              "sku": "sku_stale_1",
              "quantity": 1,
              "created_by": "bad_runner",
              "source_event_id": "task_promise_3001",
              "based_on_available": 1,
              "true_available_at_commit": 0,
              "snapshot_version": "stale",
              "last_synced_at": "stale",
              "reservation_id": null
            }
          },
          {
            "step": 4,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: reservation_required_before_promise (critical).",
            "details": {
              "policy_id": "reservation_required_before_promise",
              "severity": "critical",
              "status": "failed",
              "evidence": {
                "promise_id": "promise_001",
                "order_id": "order_3001",
                "sku": "sku_stale_1",
                "quantity": 1,
                "based_on_available": 1,
                "true_available_at_commit": 0,
                "reservation_id": null,
                "matching_reservations": []
              },
              "business_impact": "The automation promised fulfillment without reserving inventory for this order. If the visible stock was stale, the seller can oversell and later cancel or disappoint the customer.",
              "recommendation": "Reserve inventory for the order before promising fulfillment. If fresh inventory cannot be reserved, route the order to manual review."
            }
          },
          {
            "step": 5,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: no_inventory_commit_from_stale_snapshot (high).",
            "details": {
              "policy_id": "no_inventory_commit_from_stale_snapshot",
              "severity": "high",
              "status": "failed",
              "evidence": {
                "promise_id": "promise_001",
                "order_id": "order_3001",
                "sku": "sku_stale_1",
                "quantity": 1,
                "based_on_available": 1,
                "true_available_at_commit": 0,
                "stale_markers": {
                  "last_synced_at": "stale",
                  "snapshot_version": "stale"
                }
              },
              "business_impact": "The automation committed a fulfillment promise from an outdated inventory snapshot. Stale stock data can turn a normal order into an oversell incident.",
              "recommendation": "Refresh inventory before committing customer-facing promises, and block or review the action when the inventory snapshot is stale."
            }
          },
          {
            "step": 6,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: no_oversell (critical).",
            "details": {
              "policy_id": "no_oversell",
              "severity": "critical",
              "status": "failed",
              "evidence": {
                "promise_id": "promise_001",
                "order_id": "order_3001",
                "sku": "sku_stale_1",
                "promised_quantity": 1,
                "true_available_at_commit": 0,
                "oversell_quantity": 1
              },
              "business_impact": "The automation promised more units than were truly available, creating cancellation, backorder, extra support, and review risk.",
              "recommendation": "Only promise fulfillment after a successful reservation against fresh available inventory."
            }
          }
        ],
        "signals": {
          "unreserved_fulfillment_promise": true,
          "oversell_risk": true
        },
        "counts": {
          "fulfillments": {
            "before": 0,
            "after": 0
          },
          "promises": {
            "before": 0,
            "after": 1
          },
          "refunds": {
            "before": 0,
            "after": 0
          },
          "approvalRequests": {
            "before": 0,
            "after": 0
          },
          "inventoryReleases": {
            "before": 0,
            "after": 0
          },
          "workflowHolds": {
            "before": 0,
            "after": 0
          },
          "warehouseCancellationRequests": {
            "before": 0,
            "after": 0
          }
        }
      },
      "good": {
        "status": "passed",
        "runId": "run_20260529T063818049896Z_SCN-003_good_runner",
        "findings": [],
        "timeline": [
          {
            "step": 1,
            "actor": "scenario",
            "event": "inventory_promise_task_received",
            "message": "Inventory promise task task_promise_3001 received for order order_3001 with fault stale_inventory_snapshot.",
            "details": {
              "type": "inventory_promise_task",
              "id": "task_promise_3001",
              "order_id": "order_3001",
              "fault": {
                "type": "stale_inventory_snapshot"
              }
            }
          },
          {
            "step": 2,
            "actor": "good_runner",
            "event": "inventory_refreshed",
            "message": "good_runner refreshes inventory for sku_stale_1; available is now 0.",
            "details": {
              "before": {
                "sku": "sku_stale_1",
                "on_hand": 1,
                "reserved": 1,
                "available": 1,
                "committed": 1,
                "true_available": 0,
                "source_version": "stale",
                "last_synced_at": "stale"
              },
              "after": {
                "sku": "sku_stale_1",
                "on_hand": 1,
                "reserved": 1,
                "available": 0,
                "committed": 1,
                "true_available": 0,
                "source_version": "refreshed",
                "last_synced_at": "fresh"
              }
            }
          },
          {
            "step": 3,
            "actor": "good_runner",
            "event": "manual_review_routed",
            "message": "good_runner routes order order_3001, sku sku_stale_1 to manual review.",
            "details": {
              "order_id": "order_3001",
              "sku": "sku_stale_1",
              "reason": "fresh_inventory_unavailable",
              "source_event_id": "task_promise_3001"
            }
          },
          {
            "step": 4,
            "actor": "policy_engine",
            "event": "policy_check_passed",
            "message": "Policy check passed with no violations.",
            "details": {
              "status": "passed"
            }
          }
        ],
        "signals": {},
        "counts": {
          "fulfillments": {
            "before": 0,
            "after": 0
          },
          "promises": {
            "before": 0,
            "after": 0
          },
          "refunds": {
            "before": 0,
            "after": 0
          },
          "approvalRequests": {
            "before": 0,
            "after": 0
          },
          "inventoryReleases": {
            "before": 0,
            "after": 0
          },
          "workflowHolds": {
            "before": 0,
            "after": 0
          },
          "warehouseCancellationRequests": {
            "before": 0,
            "after": 0
          }
        }
      }
    },
    {
      "id": "SCN-004",
      "slug": "SCN-004_refund_after_shipment_bypass",
      "title": "Refund After Shipment Approval Bypass",
      "accident": "订单已经发货且 carrier scanned，自动化仍直接退款。",
      "businessLoss": "钱货两失、高额退款失控、售后审批失效。",
      "badBehavior": "坏流程不检查 shipment state，也不创建 approval request，直接 issue refund。",
      "goodBehavior": "好流程发现已发货和高金额风险，创建审批并 hold refund。",
      "fix": "发货后退款和高额退款必须进入审批；审批前不得 issue refund。",
      "gate": "上线前模拟 shipped refund request；只要直接退款，就阻止发布。",
      "risk": "no_refund_after_shipment_without_approval",
      "impact": "The automation issued a refund after the shipment had already left the controllable fulfillment stage. This can create money-plus-goods loss and manual recovery work.",
      "recommendation": "When an order is shipped or carrier-scanned, create an approval request and hold the refund until a reviewer confirms the correct after-shipment action.",
      "bad": {
        "status": "failed",
        "runId": "run_20260529T063819776100Z_SCN-004_bad_runner",
        "findings": [
          {
            "policy_id": "no_refund_after_shipment_without_approval",
            "severity": "critical",
            "status": "failed",
            "evidence": {
              "refund_id": "refund_001",
              "order_id": "order_4001",
              "amount": 120.0,
              "reason": "buyer_changed_mind",
              "fulfillment_status_at_issue": "shipped",
              "shipment_status_at_issue": "carrier_scanned",
              "approval_id": null,
              "approved_by": null,
              "source_event_id": "refund_req_4001"
            },
            "business_impact": "The automation issued a refund after the shipment had already left the controllable fulfillment stage. This can create money-plus-goods loss and manual recovery work.",
            "recommendation": "When an order is shipped or carrier-scanned, create an approval request and hold the refund until a reviewer confirms the correct after-shipment action."
          },
          {
            "policy_id": "high_value_refund_requires_approval",
            "severity": "high",
            "status": "failed",
            "evidence": {
              "refund_id": "refund_001",
              "order_id": "order_4001",
              "amount": 120.0,
              "threshold": 100.0,
              "approval_id": null,
              "approved_by": null,
              "source_event_id": "refund_req_4001"
            },
            "business_impact": "The automation issued a high-value refund without approval, increasing avoidable cash-loss and fraud risk.",
            "recommendation": "Route refunds at or above the high-value threshold into an approval workflow before issuing money back to the buyer."
          }
        ],
        "timeline": [
          {
            "step": 1,
            "actor": "scenario",
            "event": "refund_request_received",
            "message": "Refund request refund_req_4001 received for order order_4001 in the amount of 120.",
            "details": {
              "type": "refund_request",
              "id": "refund_req_4001",
              "order_id": "order_4001",
              "amount": 120,
              "reason": "buyer_changed_mind"
            }
          },
          {
            "step": 2,
            "actor": "bad_runner",
            "event": "refund_request_processing_started",
            "message": "bad_runner starts refund request refund_req_4001 without checking shipment approval requirements.",
            "details": {
              "request_id": "refund_req_4001",
              "order_id": "order_4001",
              "fulfillment_status": "shipped",
              "shipment_status": "carrier_scanned",
              "amount": 120
            }
          },
          {
            "step": 3,
            "actor": "bad_runner",
            "event": "refund_issued",
            "message": "bad_runner issues refund refund_001 for order order_4001 without blocking platform mutation.",
            "details": {
              "refund_id": "refund_001",
              "order_id": "order_4001",
              "amount": 120.0,
              "reason": "buyer_changed_mind",
              "created_by": "bad_runner",
              "source_event_id": "refund_req_4001",
              "approval_id": null,
              "approved_by": null,
              "order_fulfillment_status_at_issue": "shipped",
              "shipment_status_at_issue": "carrier_scanned"
            }
          },
          {
            "step": 4,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: no_refund_after_shipment_without_approval (critical).",
            "details": {
              "policy_id": "no_refund_after_shipment_without_approval",
              "severity": "critical",
              "status": "failed",
              "evidence": {
                "refund_id": "refund_001",
                "order_id": "order_4001",
                "amount": 120.0,
                "reason": "buyer_changed_mind",
                "fulfillment_status_at_issue": "shipped",
                "shipment_status_at_issue": "carrier_scanned",
                "approval_id": null,
                "approved_by": null,
                "source_event_id": "refund_req_4001"
              },
              "business_impact": "The automation issued a refund after the shipment had already left the controllable fulfillment stage. This can create money-plus-goods loss and manual recovery work.",
              "recommendation": "When an order is shipped or carrier-scanned, create an approval request and hold the refund until a reviewer confirms the correct after-shipment action."
            }
          },
          {
            "step": 5,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: high_value_refund_requires_approval (high).",
            "details": {
              "policy_id": "high_value_refund_requires_approval",
              "severity": "high",
              "status": "failed",
              "evidence": {
                "refund_id": "refund_001",
                "order_id": "order_4001",
                "amount": 120.0,
                "threshold": 100.0,
                "approval_id": null,
                "approved_by": null,
                "source_event_id": "refund_req_4001"
              },
              "business_impact": "The automation issued a high-value refund without approval, increasing avoidable cash-loss and fraud risk.",
              "recommendation": "Route refunds at or above the high-value threshold into an approval workflow before issuing money back to the buyer."
            }
          }
        ],
        "signals": {
          "post_shipment_refund_without_approval": true,
          "high_value_refund_without_approval": true
        },
        "counts": {
          "fulfillments": {
            "before": 0,
            "after": 0
          },
          "promises": {
            "before": 0,
            "after": 0
          },
          "refunds": {
            "before": 0,
            "after": 1
          },
          "approvalRequests": {
            "before": 0,
            "after": 0
          },
          "inventoryReleases": {
            "before": 0,
            "after": 0
          },
          "workflowHolds": {
            "before": 0,
            "after": 0
          },
          "warehouseCancellationRequests": {
            "before": 0,
            "after": 0
          }
        }
      },
      "good": {
        "status": "passed",
        "runId": "run_20260529T063819780760Z_SCN-004_good_runner",
        "findings": [],
        "timeline": [
          {
            "step": 1,
            "actor": "scenario",
            "event": "refund_request_received",
            "message": "Refund request refund_req_4001 received for order order_4001 in the amount of 120.",
            "details": {
              "type": "refund_request",
              "id": "refund_req_4001",
              "order_id": "order_4001",
              "amount": 120,
              "reason": "buyer_changed_mind"
            }
          },
          {
            "step": 2,
            "actor": "good_runner",
            "event": "refund_request_processing_started",
            "message": "good_runner checks shipment state before refunding order order_4001.",
            "details": {
              "request_id": "refund_req_4001",
              "order_id": "order_4001",
              "fulfillment_status": "shipped",
              "shipment_status": "carrier_scanned",
              "amount": 120
            }
          },
          {
            "step": 3,
            "actor": "good_runner",
            "event": "approval_request_created",
            "message": "good_runner creates approval request approval_001 before refunding order order_4001.",
            "details": {
              "approval_id": "approval_001",
              "order_id": "order_4001",
              "amount": 120.0,
              "reason": "buyer_changed_mind",
              "created_by": "good_runner",
              "source_event_id": "refund_req_4001",
              "status": "pending",
              "required_policy": "no_refund_after_shipment_without_approval"
            }
          },
          {
            "step": 4,
            "actor": "good_runner",
            "event": "refund_held_for_review",
            "message": "good_runner holds refund request refund_req_4001 until approval request approval_001 is reviewed.",
            "details": {
              "request_id": "refund_req_4001",
              "approval_id": "approval_001",
              "order_id": "order_4001",
              "required_policy": "no_refund_after_shipment_without_approval"
            }
          },
          {
            "step": 5,
            "actor": "policy_engine",
            "event": "policy_check_passed",
            "message": "Policy check passed with no violations.",
            "details": {
              "status": "passed"
            }
          }
        ],
        "signals": {},
        "counts": {
          "fulfillments": {
            "before": 0,
            "after": 0
          },
          "promises": {
            "before": 0,
            "after": 0
          },
          "refunds": {
            "before": 0,
            "after": 0
          },
          "approvalRequests": {
            "before": 0,
            "after": 1
          },
          "inventoryReleases": {
            "before": 0,
            "after": 0
          },
          "workflowHolds": {
            "before": 0,
            "after": 0
          },
          "warehouseCancellationRequests": {
            "before": 0,
            "after": 0
          }
        }
      }
    },
    {
      "id": "SCN-005",
      "slug": "SCN-005_cancel_after_pick_pack_conflict",
      "title": "Cancel After Pick/Pack Warehouse Conflict",
      "accident": "买家取消和仓库 pick/pack 撞车，自动化按普通取消处理。",
      "businessLoss": "退款后仍发货、库存释放错误、仓库追货和账实不一致。",
      "badBehavior": "坏流程取消订单、释放库存、退款，但仓库继续把已 picked 包裹发出。",
      "goodBehavior": "好流程识别 warehouse conflict，创建 hold，并向仓库提交 cancellation request。",
      "fix": "picked/packed/label_created/carrier_scanned/shipped 都必须进入 hold；仓库确认前不得退款或释放库存。",
      "gate": "上线前模拟 cancel-after-pick；只要出现 refund/release/ship-after-cancel，就阻止发布。",
      "risk": "warehouse_conflict_requires_hold",
      "impact": "The automation handled a picked or packed warehouse order as if cancellation were still simple. That can produce a refund, inventory release, and outbound parcel for the same order.",
      "recommendation": "When warehouse status is picked, packed, label-created, carrier-scanned, or shipped, place the order on hold and submit a warehouse cancellation request before refunding or releasing inventory.",
      "bad": {
        "status": "failed",
        "runId": "run_20260529T063822659748Z_SCN-005_bad_runner",
        "findings": [
          {
            "policy_id": "warehouse_conflict_requires_hold",
            "severity": "critical",
            "status": "failed",
            "evidence": {
              "cancel_request_id": "cancel_req_5001",
              "order_id": "order_5001",
              "warehouse_jobs_at_request": [
                {
                  "warehouse_job_id": "wh_job_5001",
                  "order_id": "order_5001",
                  "sku": "sku_pickpack_1",
                  "quantity": 1,
                  "status": "picked",
                  "cancellation_requested": false,
                  "hold_status": null,
                  "continued_after_cancel": false
                }
              ],
              "order_status_after": "cancelled",
              "inventory_release_ids": [
                "release_001"
              ],
              "refund_ids": [
                "refund_001"
              ],
              "continued_warehouse_jobs": [
                "wh_job_5001"
              ],
              "hold_ids": [],
              "warehouse_cancellation_request_ids": []
            },
            "business_impact": "The automation handled a picked or packed warehouse order as if cancellation were still simple. That can produce a refund, inventory release, and outbound parcel for the same order.",
            "recommendation": "When warehouse status is picked, packed, label-created, carrier-scanned, or shipped, place the order on hold and submit a warehouse cancellation request before refunding or releasing inventory."
          },
          {
            "policy_id": "no_ship_after_cancel",
            "severity": "critical",
            "status": "failed",
            "evidence": {
              "order_id": "order_5001",
              "warehouse_job_id": "wh_job_5001",
              "warehouse_status_after": "shipped",
              "continued_after_cancel": true,
              "order_status_after": "cancelled",
              "shipment_status_after": "shipped"
            },
            "business_impact": "The warehouse continued fulfillment after the order was marked cancelled, creating wrong-shipment and customer support recovery risk.",
            "recommendation": "Do not mark the order cancelled or clear downstream actions until the warehouse confirms the pick/pack job has been stopped."
          },
          {
            "policy_id": "no_double_refund_or_inventory_release",
            "severity": "high",
            "status": "failed",
            "evidence": {
              "order_id": "order_5001",
              "inventory_release_ids": [
                "release_001"
              ],
              "refund_ids": [
                "refund_001"
              ],
              "continued_warehouse_jobs": [
                "wh_job_5001"
              ],
              "warehouse_statuses_after": [
                "shipped"
              ]
            },
            "business_impact": "The automation refunded the buyer and released inventory while the warehouse still shipped the goods. This creates money loss plus inventory ledger mismatch.",
            "recommendation": "Keep refund and inventory release pending until warehouse cancellation is confirmed. Resolve the warehouse state first, then perform the financial and inventory actions."
          }
        ],
        "timeline": [
          {
            "step": 1,
            "actor": "scenario",
            "event": "cancel_request_received",
            "message": "Cancel request cancel_req_5001 received for order order_5001.",
            "details": {
              "type": "cancel_request",
              "id": "cancel_req_5001",
              "order_id": "order_5001",
              "amount": 80,
              "reason": "buyer_cancelled",
              "warehouse_jobs_at_request": [
                {
                  "warehouse_job_id": "wh_job_5001",
                  "order_id": "order_5001",
                  "sku": "sku_pickpack_1",
                  "quantity": 1,
                  "status": "picked",
                  "cancellation_requested": false,
                  "hold_status": null,
                  "continued_after_cancel": false
                }
              ]
            }
          },
          {
            "step": 2,
            "actor": "bad_runner",
            "event": "cancel_request_processing_started",
            "message": "bad_runner treats cancel request cancel_req_5001 as a simple order cancellation despite warehouse progress.",
            "details": {
              "request_id": "cancel_req_5001",
              "order_id": "order_5001",
              "warehouse_jobs_at_request": []
            }
          },
          {
            "step": 3,
            "actor": "bad_runner",
            "event": "order_cancelled",
            "message": "bad_runner marks order order_5001 as cancelled.",
            "details": {
              "source_event_id": "cancel_req_5001",
              "before": {
                "order_id": "order_5001",
                "payment_status": "paid",
                "order_status": "open",
                "line_items": [
                  {
                    "sku": "sku_pickpack_1",
                    "quantity": 1
                  }
                ],
                "fulfillment_status": "submitted_to_warehouse",
                "shipment_status": "not_shipped",
                "refund_status": "none",
                "captured_amount": 80.0,
                "cancel_requested": true
              },
              "after": {
                "order_id": "order_5001",
                "payment_status": "paid",
                "order_status": "cancelled",
                "line_items": [
                  {
                    "sku": "sku_pickpack_1",
                    "quantity": 1
                  }
                ],
                "fulfillment_status": "submitted_to_warehouse",
                "shipment_status": "not_shipped",
                "refund_status": "none",
                "captured_amount": 80.0,
                "cancel_requested": true
              }
            }
          },
          {
            "step": 4,
            "actor": "bad_runner",
            "event": "inventory_released",
            "message": "bad_runner releases 1 unit(s) of sku_pickpack_1; reserved inventory is now 0.",
            "details": {
              "release_id": "release_001",
              "order_id": "order_5001",
              "sku": "sku_pickpack_1",
              "quantity": 1,
              "created_by": "bad_runner",
              "source_event_id": "cancel_req_5001",
              "warehouse_status_at_release": "picked",
              "order_status_at_release": "cancelled"
            }
          },
          {
            "step": 5,
            "actor": "bad_runner",
            "event": "refund_issued",
            "message": "bad_runner issues refund refund_001 for order order_5001 without blocking platform mutation.",
            "details": {
              "refund_id": "refund_001",
              "order_id": "order_5001",
              "amount": 80.0,
              "reason": "buyer_cancelled",
              "created_by": "bad_runner",
              "source_event_id": "cancel_req_5001",
              "approval_id": null,
              "approved_by": null,
              "order_fulfillment_status_at_issue": "submitted_to_warehouse",
              "shipment_status_at_issue": "not_shipped"
            }
          },
          {
            "step": 6,
            "actor": "warehouse_twin",
            "event": "warehouse_fulfillment_continued",
            "message": "Warehouse continues job wh_job_5001 for cancelled order order_5001; status is now shipped.",
            "details": {
              "source_event_id": "cancel_req_5001",
              "triggered_by": "bad_runner",
              "before": {
                "warehouse_job_id": "wh_job_5001",
                "order_id": "order_5001",
                "sku": "sku_pickpack_1",
                "quantity": 1,
                "status": "picked",
                "cancellation_requested": false,
                "hold_status": null,
                "continued_after_cancel": false
              },
              "after": {
                "warehouse_job_id": "wh_job_5001",
                "order_id": "order_5001",
                "sku": "sku_pickpack_1",
                "quantity": 1,
                "status": "shipped",
                "cancellation_requested": false,
                "hold_status": null,
                "continued_after_cancel": true
              }
            }
          },
          {
            "step": 7,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: warehouse_conflict_requires_hold (critical).",
            "details": {
              "policy_id": "warehouse_conflict_requires_hold",
              "severity": "critical",
              "status": "failed",
              "evidence": {
                "cancel_request_id": "cancel_req_5001",
                "order_id": "order_5001",
                "warehouse_jobs_at_request": [
                  {
                    "warehouse_job_id": "wh_job_5001",
                    "order_id": "order_5001",
                    "sku": "sku_pickpack_1",
                    "quantity": 1,
                    "status": "picked",
                    "cancellation_requested": false,
                    "hold_status": null,
                    "continued_after_cancel": false
                  }
                ],
                "order_status_after": "cancelled",
                "inventory_release_ids": [
                  "release_001"
                ],
                "refund_ids": [
                  "refund_001"
                ],
                "continued_warehouse_jobs": [
                  "wh_job_5001"
                ],
                "hold_ids": [],
                "warehouse_cancellation_request_ids": []
              },
              "business_impact": "The automation handled a picked or packed warehouse order as if cancellation were still simple. That can produce a refund, inventory release, and outbound parcel for the same order.",
              "recommendation": "When warehouse status is picked, packed, label-created, carrier-scanned, or shipped, place the order on hold and submit a warehouse cancellation request before refunding or releasing inventory."
            }
          },
          {
            "step": 8,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: no_ship_after_cancel (critical).",
            "details": {
              "policy_id": "no_ship_after_cancel",
              "severity": "critical",
              "status": "failed",
              "evidence": {
                "order_id": "order_5001",
                "warehouse_job_id": "wh_job_5001",
                "warehouse_status_after": "shipped",
                "continued_after_cancel": true,
                "order_status_after": "cancelled",
                "shipment_status_after": "shipped"
              },
              "business_impact": "The warehouse continued fulfillment after the order was marked cancelled, creating wrong-shipment and customer support recovery risk.",
              "recommendation": "Do not mark the order cancelled or clear downstream actions until the warehouse confirms the pick/pack job has been stopped."
            }
          },
          {
            "step": 9,
            "actor": "policy_engine",
            "event": "policy_violation_detected",
            "message": "Policy violation detected: no_double_refund_or_inventory_release (high).",
            "details": {
              "policy_id": "no_double_refund_or_inventory_release",
              "severity": "high",
              "status": "failed",
              "evidence": {
                "order_id": "order_5001",
                "inventory_release_ids": [
                  "release_001"
                ],
                "refund_ids": [
                  "refund_001"
                ],
                "continued_warehouse_jobs": [
                  "wh_job_5001"
                ],
                "warehouse_statuses_after": [
                  "shipped"
                ]
              },
              "business_impact": "The automation refunded the buyer and released inventory while the warehouse still shipped the goods. This creates money loss plus inventory ledger mismatch.",
              "recommendation": "Keep refund and inventory release pending until warehouse cancellation is confirmed. Resolve the warehouse state first, then perform the financial and inventory actions."
            }
          }
        ],
        "signals": {
          "warehouse_conflict_without_hold": true,
          "ship_after_cancel": true,
          "refund_and_inventory_release_while_warehouse_continued": true
        },
        "counts": {
          "fulfillments": {
            "before": 0,
            "after": 0
          },
          "promises": {
            "before": 0,
            "after": 0
          },
          "refunds": {
            "before": 0,
            "after": 1
          },
          "approvalRequests": {
            "before": 0,
            "after": 0
          },
          "inventoryReleases": {
            "before": 0,
            "after": 1
          },
          "workflowHolds": {
            "before": 0,
            "after": 0
          },
          "warehouseCancellationRequests": {
            "before": 0,
            "after": 0
          }
        }
      },
      "good": {
        "status": "passed",
        "runId": "run_20260529T063822672754Z_SCN-005_good_runner",
        "findings": [],
        "timeline": [
          {
            "step": 1,
            "actor": "scenario",
            "event": "cancel_request_received",
            "message": "Cancel request cancel_req_5001 received for order order_5001.",
            "details": {
              "type": "cancel_request",
              "id": "cancel_req_5001",
              "order_id": "order_5001",
              "amount": 80,
              "reason": "buyer_cancelled",
              "warehouse_jobs_at_request": [
                {
                  "warehouse_job_id": "wh_job_5001",
                  "order_id": "order_5001",
                  "sku": "sku_pickpack_1",
                  "quantity": 1,
                  "status": "picked",
                  "cancellation_requested": false,
                  "hold_status": null,
                  "continued_after_cancel": false
                }
              ]
            }
          },
          {
            "step": 2,
            "actor": "good_runner",
            "event": "cancel_request_processing_started",
            "message": "good_runner checks warehouse progress before resolving cancel request cancel_req_5001.",
            "details": {
              "request_id": "cancel_req_5001",
              "order_id": "order_5001",
              "warehouse_jobs_at_request": []
            }
          },
          {
            "step": 3,
            "actor": "good_runner",
            "event": "workflow_hold_created",
            "message": "good_runner places order order_5001 on hold for warehouse_pick_pack_conflict.",
            "details": {
              "hold_id": "hold_001",
              "order_id": "order_5001",
              "sku": "sku_pickpack_1",
              "reason": "warehouse_pick_pack_conflict",
              "created_by": "good_runner",
              "source_event_id": "cancel_req_5001",
              "warehouse_status_at_hold": "picked"
            }
          },
          {
            "step": 4,
            "actor": "good_runner",
            "event": "warehouse_cancellation_requested",
            "message": "good_runner asks warehouse to cancel job wh_job_5001 while status is picked.",
            "details": {
              "cancellation_request_id": "wh_cancel_001",
              "order_id": "order_5001",
              "warehouse_job_id": "wh_job_5001",
              "created_by": "good_runner",
              "source_event_id": "cancel_req_5001",
              "status": "requested",
              "warehouse_status_at_request": "picked"
            }
          },
          {
            "step": 5,
            "actor": "good_runner",
            "event": "cancel_resolution_held",
            "message": "good_runner does not refund, release inventory, or mark order order_5001 cancelled until warehouse confirms the stop.",
            "details": {
              "request_id": "cancel_req_5001",
              "order_id": "order_5001",
              "held_actions": [
                "cancel_order",
                "release_inventory",
                "issue_refund"
              ]
            }
          },
          {
            "step": 6,
            "actor": "policy_engine",
            "event": "policy_check_passed",
            "message": "Policy check passed with no violations.",
            "details": {
              "status": "passed"
            }
          }
        ],
        "signals": {},
        "counts": {
          "fulfillments": {
            "before": 0,
            "after": 0
          },
          "promises": {
            "before": 0,
            "after": 0
          },
          "refunds": {
            "before": 0,
            "after": 0
          },
          "approvalRequests": {
            "before": 0,
            "after": 0
          },
          "inventoryReleases": {
            "before": 0,
            "after": 0
          },
          "workflowHolds": {
            "before": 0,
            "after": 1
          },
          "warehouseCancellationRequests": {
            "before": 0,
            "after": 1
          }
        }
      }
    }
  ]
};
