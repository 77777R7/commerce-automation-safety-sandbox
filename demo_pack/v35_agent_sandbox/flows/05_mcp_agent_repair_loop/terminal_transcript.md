$ MCP commerce.start_session(SCN-002) -> session sess_20260530T092502042629Z_SCN-002_382c2244
$ MCP commerce.get_task -> task_fulfill_2001 fault=timeout_after_commit
$ MCP commerce.create_fulfillment(request_id=mcp_req_timeout_1) -> ok=False error=timeout_after_commit; side effect committed
$ MCP commerce.create_fulfillment(request_id=mcp_req_retry_2) -> fulfillment=ful_002
$ MCP commerce.complete_session -> failed findings=['idempotency_required_for_mutating_retries', 'no_duplicate_fulfillment']
$ MCP commerce.get_trace -> 6 timeline events
$ MCP commerce.get_policy_report -> ['idempotency_required_for_mutating_retries', 'no_duplicate_fulfillment']
$ MCP commerce.get_patch_hints -> 2 repair hints
