# Replacement implementation review — initial pass
Reviewer /root/bridgend_review; read-only source/evidence review. No implementation edits, registration or inquiry submission. Reviewed app/*.py, templates, tools/import_source.py, tools/backup.py and tests/test_app.py. Existing five test groups are useful smoke coverage, not complete replacement/security/recovery acceptance.

## Conclusion
LOCAL IMPLEMENTATION ACCEPTANCE = FAIL pending defects below. COMPLETE REPLACEMENT = NOT READY. Flask/Jinja + SQLite + Waitress is reasonable for a single-owner catalogue/inquiry application with same-origin SSR, given available runtime and no paid external services. The DS-002B React/Express/Prisma defaults do not justify gratuitous rewrites: document this task-specific deviation, exact versions, parameterizedSQL, schema migration plan and productionSQLite constraints. Existing blueprint separation is sound, though route functions currently contain much business logic. No conclusion of production readiness.

## Actionable findings

### P1 — Draft/unpublished media remains publicly accessible
app/storefront.py:85–89 authorises media solely by rights/path, never joins products or checks draft status. An uploaded image can be obtained anonymously by its known URL while its product is draft or after withdrawal. Hash filenames are identifiers, not access control. Restrict public route to media referenced by public products; provide authenticated preview for drafts and ensure browser cache policy matches withdrawal expectations. Regression: upload to draft in isolated testDB, anonymous media404, admin preview succeeds; publish then withdraw and verify anonymous denial.

### P1 — Newly published products are not reliably newest
app/storefront.py home/catalogue use CAST(substr(id,7) AS INTEGER); app/admin.py:41 creates BA+random hex IDs. New stock ordering becomes random/zero based on characters in its ID, and source IDs also conflate source reference with recency. A new published piece may remain behind old imported stock and never reach four-item homepage. Add explicit created/published ordering field or reliable monotonic sequence; deterministic tie-break. Regression: create two products with adversarialIDs and verify publish order in home/catalogue. Do not replace by updated_at alone if an edit should not relist old stock.

### P2 — Saving shop telephone numbers changes labels but not dial targets
app/admin.py:96–102 allows phone/mobile settings; templates/contact.html hardcodes tel:+442893341979 / tel:+447966751699. After correction the visitor sees new contact information but calls the old number. Store/validate canonical phone targets and derive both label and href. Same issue for changed address vs hardcoded Google Maps query. Check all templates for hardcoded identity/config after settings edits.

### P2 — Selling CTA opens a buying inquiry
home.html uses /contact?topic=Selling, but storefront.contact passes values={} and contact template defaults to first option Buying an item. Preserve and whitelist intended topic using canonical allowed value, including service-specific routes where intended. Regression: follow seller CTA and assert selectedSelling an item; item inquiry remainsBuying an item.

### P2 — Conflicting hours silently replaced by one schedule
tools/import_source.py:28 seeds exact10:30–17:30 plusSunday closed despite earlier explicit Atlas/Yell conflict. No new corroborating evidence is supplied by the code. Reuse call-before-travel or visibly source-label unresolved schedule; do not silently select one as current verified truth. Any updated live proof can resolve this with an evidence receipt.

### P2 — Concurrent admin edits silently overwrite each other
app/admin.py:23/43 reads product and upserts without submitted revision check. Two tabs editing same record cause later save to discard earlier status/price/content changes. Add version token/conditional update and409 with recovery preserving submitted values. Test two clients/tabs editing same row; second stale save must not overwrite.

### P2 — Enquiries lose the original item context after product edits
inquiries schema only keeps product_id; storefront.enquire inserts no item title/reference/price/status snapshot. Admin inquiry page shows bare ID. Editing/referencing product later leaves operator unable to recover what visitor saw when enquiring. Store minimal immutable product snapshot transactionally with inquiry, display it in inbox detail with current product link. Test inquiry then edit product; original snapshot remains.

### P2 — Management lifecycle is incomplete
admin.py provides category selection only; no category add/rename/archive. Images can be added/reordered but never removed/withdrawn or havealt corrected, so a wrong upload cannot be corrected through admin. Inquiry list LIMIT500 has no pagination/search; product list LIMIT400 similarly hides older records after growth. These are concrete gaps against self-managed inventory/inquiries, not optional cosmetic features. Add minimal safe category lifecycle and image detach/withdraw actions withCSRF/audit, plus bounded pagination/search. Removal means reversible record detach/archive; do not delete original source/media files casually.

## Recovery and migration gaps
backup.py usesSQLite backupAPI and restore into a new directory, correctly avoiding liveoverwrite; it deliberately clears sessions. Good baseline. tests/test_app.py:test_05 only checks productcount>=282 and cleared sessions, not inquiry/outbox/media/category/settings equivalence, digest equality, restart/login or corrupt backup rejection. BackupDB then media copy is not a single application snapshot if uploads can race: document/quiesce writes during consistentDB+media snapshot or design immutable media inclusion/retry verification. Test a saved inquiry, uploaded fixture image and admin edit before backup; restore to separate runtime and compare required records/media, verify signin with existing hash, output measuredRTO. Never destroy source fixture/runtime during review.

db.py unconditionally executes CREATE IF NOT EXISTS and PRAGMA user_version=1 on startup. No migration runner or upgrade detection exists; as schema changes this can silently mislabel an incompatibleDB. Add explicit version check and sequential transactional migrations before claiming maintainable replacement. Current code can bootstrap an emptyDB, which is not proof of upgrade safety.

## Security/test limits
Positive evidence: parameterizedSQL, scrypt password hashes, hashed revocable sessions,8-hour expiry, HttpOnly/SameSite cookie, CSRF+origin check, restrictiveCSP, bound image formats/dimensions, public inquiry idempotency/outbox transaction. Tests cover logout replay denial and escapedstoredXSS but not expiry, hostileOrigin, loginthrottle, malformed/oversizedimage, draftimageprivacy, stale edits, duplicate-categorypayload, DB failure zero-write, or productionsecure-cookie fail-closed configuration. Add targeted regression tests for discovered defects first; do not claim security from five grouped smoke tests.

## Explicit remaining replacement boundaries
282records/65active217sold/28categories/1438source imageURLs are import result claims; source reconciliation should include uniqueIDs, missing fields and exactstatus counts rather than onlyexpectedtotals. Imported imageURLs are not imported usable photographs. Pendingrights/path means no product photos; image-note text is an honest fallback but cannot equal complete visual/catalogue replacement. Keep media coverage and current user authorisation separate. No license inferred from full-site scope, no watermark removal, no generated actual-product substitutes.

Local inquiries save to DB/outbox; no productionmail sending implemented/authorised. Receipt must not be represented to user as actual customer communication. Productioncredentials/domain/SMTP/HTTPS/monitoring/customeracceptance and final assetrights remainNOT VERIFIED. Preserve prior accepted staticartifact independently; its8.65 does not carry to newroutes/backend.

Recommendednext: fixP1s and configuration/topic defects in activeimplementation, fill minimaloperator lifecycle, strengthen targetedsecurity/recovery tests, then submit currentcodehash + sourcecoverage + browser evidence for follow-up review. No production or client-facing complete-replacementPASS until correspondingdependencies are satisfied.
