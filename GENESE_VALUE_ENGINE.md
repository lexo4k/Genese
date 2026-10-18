# GÊNESE Value Discovery Engine (MVP)

## Purpose

The first implementation is an evidence-first engine for evaluating candidate sources of legitimate, redeemable value. It is not a mining system, a money generator, or a tool for accessing private accounts.

## Current behavior

- Accepts candidate records from explicitly configured sources.
- Checks that the source and evidence links use HTTPS.
- Requires a positive amount, issuer reference, redemption method, and explicit source and authorization confirmations.
- Labels incomplete candidates `needs_verification`.
- Labels a candidate `verified_receivable` only when every required evidence field is present.
- Keeps evaluation separate from any Mercado Pago transaction. A verified candidate is not proof that a transfer has happened.

## Important limitation

This MVP evaluates records supplied to it. It does **not yet discover opportunities on its own**, connect to external source providers, or transfer funds. Provider adapters must be implemented one at a time for sources that explicitly publish an authorized redemption flow. Each adapter needs tests and documented terms.

The Mercado Pago webhook is a notification channel, not a source of funds. Real receipts must be verified against the provider's authenticated records and reconciled with the merchant account.

## Test

Run:

```bash
python -m unittest discover -s tests -v
```

This code does not claim to generate revenue. It establishes the evidence and verification boundary needed before connecting legitimate sources.
