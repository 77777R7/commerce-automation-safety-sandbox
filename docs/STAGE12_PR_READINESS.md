# Stage 12 PR Readiness

Stage 12 adds the first platform-shaped digital twin skin:

```txt
Shopify-shaped request -> normalized commerce action/event -> permissive twin -> policy check
```

This PR should stay limited to Shopify-like Skin V0 and its gate wiring.

## Include In PR

- `commerce-safety-sandbox/commerce_safety/platform_skins/`
- `commerce-safety-sandbox/commerce_safety/live/http_api.py`
- `docs/SHOPIFY_LIKE_SKIN_V0.md`
- `docs/openapi/live_twin_api.yaml`
- `docs/openapi/schemathesis_warning_allowlist.yaml`
- Stage 12 tests:
  - `tests/test_shopify_skin_manifests.py`
  - `tests/test_shopify_webhook_mapper.py`
  - `tests/test_shopify_graphql_router.py`
  - `tests/test_shopify_skin_live_http.py`
  - `tests/test_openapi_contract_shape.py`
- Stage 12 smoke harness:
  - `tools/stage12_shopify_skin_harness.py`
  - `tools/smoke_stage12_shopify_skin_v0.sh`
- Source-of-truth updates:
  - `README.md`
  - `ROADMAP.md`
  - `MVP_ACCEPTANCE.md`
  - `AGENTS.md`
  - `tools/smoke_stage0_rebaseline.sh`
  - `tools/smoke_stage9_api_hardening.sh`
  - `tools/smoke_v35.sh`

## Exclude From PR

Keep these out of the Stage 12 PR unless a separate PR explicitly owns them:

- Generated `demo_pack/` report refreshes.
- Generated `demo_viewer/demo-data.js` refreshes.
- Failure Intelligence collector or scenario discovery experiments.
- Reddit/source collection scripts.
- Python `__pycache__/` and `*.pyc` files.

## Required Gates

```bash
python3 -m pytest tests/test_shopify_skin_manifests.py tests/test_shopify_webhook_mapper.py tests/test_shopify_graphql_router.py tests/test_shopify_skin_live_http.py tests/test_openapi_contract_shape.py
./tools/smoke_stage12_shopify_skin_v0.sh
PYTHON=python3.12 ./tools/smoke_v35.sh
```

## Merge Notes

- This stage is an adapter layer, not a full Shopify API clone.
- Unsupported Shopify mutations must return explicit stub metadata.
- Unsafe actions remain permissive and are caught by `PolicyEngine` at
  completion.
- Stage 13 Amazon work should start after this Stage 12 PR is merged or clearly
  separated into a new branch.
