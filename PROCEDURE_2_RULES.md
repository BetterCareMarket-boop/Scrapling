# Procedure 2 Rules

## Hard rule: Scrapling-only price capture

For NOVIS Procedure 2, every competitor price capture must be performed with **Scrapling**.

- Use Scrapling fetchers/parsers for all live price extraction.
- Do not fall back to requests, curl, BeautifulSoup-only fetching, TinyFish, search snippets, or another scraping engine to obtain a price.
- Other tools may be used for metadata, diagnostics, or code review, but a price is not accepted for Procedure 2 unless Scrapling captured it from the approved competitor source.
- Exact product, SKU, size, colour, variant, and pack rules still apply.
- If Scrapling cannot prove the exact variant or cannot access a valid price, return blocked / unresolved / price_not_found rather than guessing.
- When two valid prices are shown, the higher value is the regular/original price and the lower value is the special/sale price.
- Database writes remain a separate approval step unless the user explicitly authorizes them.

This rule applies to all Procedure 2 batches from P55 onward and to any future re-validation of earlier Procedure 2 batches.
