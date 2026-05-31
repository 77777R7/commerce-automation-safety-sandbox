# Design Partner DPA Notes

Stage 19 design partners should use only:

- Staging agents.
- Test workflows.
- Synthetic or redacted commerce data.
- Fake platform payloads.
- Action logs without customer PII.

Design partners should not send:

- Production store credentials.
- Real customer names, emails, phone numbers, or addresses.
- Real payment credentials.
- Real warehouse credentials.
- Live refund or fulfillment credentials.

The POC is a pre-production safety validation environment, not a production
commerce processor.
