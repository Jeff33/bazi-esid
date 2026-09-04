# Contributing

Contributions should preserve three properties: deterministic computation, explicit provenance, and safe use.

## Before opening a pull request

```bash
python3 scripts/run_esid.py self-test
python3 -m unittest discover -s tests -v
```

Also run the Skill validator when developing in an environment that provides it.

## Numeric rule changes

Any change that can alter a score, band, evidence item, normalization result, or payload must:

1. update the engine version;
2. produce the expected rule or implementation hash change;
3. update exact golden expectations rather than widening them to ranges;
4. explain the reason and migration impact;
5. retain deterministic, offline behavior unless a separately reviewed architecture change says otherwise.

Do not change generated scores only to make an individual example look more favorable.

## Documentation and claims

- Distinguish rules found in the source specification from constants introduced by Code Edition.
- Do not describe internal scores as probabilities, clinical measures, objective rankings, or scientifically validated
  predictions.
- Preserve the safety, privacy, non-discrimination, and professional-advice boundaries in `DISCLAIMER.md`.
- Do not imply affiliation with or endorsement by OpenAI or other third parties.

## Test data and privacy

- Use synthetic, public-domain, or appropriately authorized data.
- Remove names, exact addresses, contacts, account IDs, and other identifying information.
- Use neutral record IDs that do not encode identity.
- Never commit secrets, credentials, private conversations, or real-world high-impact decision datasets.

Unless explicitly marked otherwise before submission, contributions accepted into this repository are licensed under
Apache License 2.0 as described in Section 5 of the license.
