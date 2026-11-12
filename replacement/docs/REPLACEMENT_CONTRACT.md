# Bridgend Antiques — full local replacement contract
2026-09-08. Execution owner /root; independent reviewer /root/bridgend_review. User explicitly replaced the old static-only scope with complete merchant-site replacement and then authorised implementation. No production deployment, merchant/platform login, real messages, payment or published migration authorised. Old demo retained as historical local artefact; replacement/ is the sole new application root.

## Scope and architecture decision
Merchant storefront home, services, stock/category/archive browsing, product details and multi-image gallery, product-specific and general enquiries, visit/contact/hours, review-source paths, privacy/terms, operator product maintenance and enquiry inbox, backup/export/restore, legacy merchant-path redirects. Public third-party marketplace discovery/search, platform accounts, platform-wide mailing lists and TV/video hosting are external platform services, not merchant-owned functions to counterfeit. Record external-link dispositions explicitly. No verified online checkout or self-service booking found; existing appointments are phone-based. Payment-method/checkout UNKNOWN is not silently marked missing or invented. Cash purchasing gold/silver is a confirmed merchant offer, not a statement that all customer purchases accept cards.

Runtime: Flask3.1.3 + Jinja autoescaped server-rendered HTML, Waitress3.0.2, Python3.12, SQLite standard library WAL. Small single-merchant/single-instance app, transaction-safe writes and busy timeout; no frontend framework needed to retain the authored design. Existing static typography/colours/visual composition reused only for this same merchant. This is a deliberate deviation from the SOP's default React/Express/Prisma stack, avoiding a separate frontend API deployment; official Flask SQLite and Waitress recipes reviewed. All project dependencies in replacement/.venv; exact requirements.lock; no global installs or upgrades. WSGI request routes, persistence, security and import separated into modules. SQLite remains an L1/local choice; production fit and persistent storage/backup are explicit gates, not automatically L2.

## Acceptance mapping
| Source capability/content | Local replacement | Acceptance |
|---|---|---|
| Dealer identity/history/phone/email/address | Home/contact/settings | Values match source; admin-editable details |
| Yell service catalogue | Services page; grouped buying, valuations, restoration/house clearance; categories | Full known list mapped, no unconfirmed guarantee |
| Source opening schedules/appointment | Contact hours sourced to merchant Atlas; call-before-travel; competing Yell schedule retained in internal source ledger | Visible hours, Sunday and by-appointment handling; factual conflict disclosed internally, not hidden omission |
| Cash gold/silver buying | Selling/service copy | Explicit cash-buying distinction |
| All active inventory | /catalogue /product/<id> | Reconcile65 active by exact IDs; do not relabel archived as for-sale |
| Archived/sold | /catalogue?status=archived | Reconcile217 unique IDs with per-item source state preserved |
| Merchant categories, pagination | Local filters/search/pagination | All source categories retained, counts and no-result state |
| Images/descriptions/prices/condition/code | Product page | Multi-image, accurate source price/currency, no current stock guarantee from stale import; permissions separate |
| Product enquiry / contact form | Same-origin POST /enquire; durable SQLite inbox | All source fields+item ID, validation, durable success only after commit, admin can read; test receipt stored |
| Telephone/email/maps | Native tel/mail and external map | Working controls, no actual contact during testing |
| Reviews/rating/read-all/write-review | Source-attributed summaries/rating and original review actions | Preserve external review-system identity, no copied review-submission service |
| Source private video | Clearly labelled existing external link if retained, no fake playable embed | Not claim working video; source failure remains source issue |
| Source privacy/terms | App-specific accurate notices | Data collected, purpose, storage/contact and actual purchase flow; legal approval remains production gate |
| Product maintenance | Authenticated admin create/edit/status/categories/images | Persistent transactions, CSRF, auth expiry/revocation, validation, no destructive delete default |
| Stock migration/ongoing edits | Idempotent importer with source snapshots + override protection | Second import no duplicates/no overwrite owner-edited records |
| Recovery | SQLite online backup + clean independent restore command | Restored count/content match, no overwrite of live DB |

## Boundaries and acceptance labels
LOCAL FUNCTIONAL PASS is separate from CONTENT/MEDIA COMPLETE and PRODUCTION REPLACEMENT PASS. Image use approval pending async user question because existing rule excludes watermarks; do not strip watermarks, hotlink or show fake item pictures. Text/source/image provenance import can proceed. Local test mail stays inbox; a live staff email notification channel, production host/domain/SSL/admin account, final rights, real delivery check and customer signoff remain prerequisites to claiming replacement live. 99/199 USD is a desired one-time offer, not an accepted full-stack quote or all-inclusive ongoing-hosting promise. Costs/maintenance in COSTS_AND_HANDOVER.md.
