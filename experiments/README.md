# Public Experiments

This directory contains the publishable evidence subset for DeltaLayer v0.

- `public-deltas.jsonl`: 48 anonymized, semantically redacted records.
- `public-corpus-metrics.json`: public byte/character counts plus the original source-corpus comparison.
- `public-provenance.json`: anonymized ids, timestamps, source labels and public-record hashes.
- `phase4-summary.json`: curated continuation summary.
- `h5-summary.json`: curated H5 summary; status remains `PARTIALLY_SUPPORTED`.

The original session transcripts, source checkout, raw session ids, internal paths, fixtures, credentials and business data are intentionally excluded. The public JSONL is a redacted derivative, so its character count is not the original 10,398-character Delta JSON measurement. That original measurement is retained as a separately labeled source-corpus statistic.
