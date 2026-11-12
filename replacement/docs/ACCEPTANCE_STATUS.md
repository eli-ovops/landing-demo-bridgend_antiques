# Current acceptance — 8 September 2026

**FULL REPLACEMENT: NOT READY.** This is an implemented local application, not a production release or a complete media transfer.

## Verified local implementation
- 282 source product IDs match local IDs exactly: 65 for sale, 217 sold; 28 categories. All 282 detail routes return200, and title/description/reference/sourceURL/sourcehash are populated. evidence/coverage.json.
- Search, category filter, source archive, sorting, pagination, details, previous/next, product-specific enquiries and legacy local redirects are implemented. Historical currency guidance is labelled as dated source guidance; GBP is the purchase currency.
- Merchant services, address, source-labelled hours/conflict, contact actions, cash-buying explanation and source-attributed review summaries are present. No invented card processing or online booking.
- Durable enquiry inbox, receipts, repeated enquiries/idempotency, operator authentication/logout, product/category editing, image upload/withdrawal/preview, concurrent edit protection, item snapshots, exports and recovery are implemented.
- Seven grouped tests PASS in evidence/test-report.txt. They include actual data persistence, access denial, operator overrides on re-import, draft media isolation, conflict prevention and complete recovery comparison with restored login.
- Browser checks:1440/390/320px ×7 routes, all200, no horizontal overflow or JS errors. evidence/browser-report.json. This is not a visual9/10 assessment.
- Browser390px actual flow: search→detail→enquiry→savedreceipt→operatorsetup/login→inbox→statussave→logout→protectedexport. Synthetic data in an isolated temporary instance; no customer message sent. evidence/e2e-report.json.
- Independent reviewer closed the scoped implementation findings in ../review/replacement-IMPLEMENTATION_FOLLOWUP.md. It explicitly withholds full replacementPASS.

## Required unresolved items
1. **Product media:0/1438 usable source photos.** Source references are recorded, but existing project policy excludes watermarked images. Pending user permission for unchanged local use is required before importing. A local-use exception would not grant production/source-transfer rights. tools/import_media.py is prepared but has NOT been run.
2. Production host/domain/HTTPS/persistentstorage/admin provisioning/notification-delivery checks/customeracceptance remain unconfigured and unauthorised. No public deployment took place. Local inbox storage is proven; external email delivery is not.
3. Merchant confirmation of conflicting opening hours and purchase payment methods remains needed. Current text is qualified; unsupported claims are absent.
4. Final content/media rights and operating costs remain separate. US$99/US$199 is the user's desired offer, not a confirmed all-inclusive full-stack quote. See COSTS_AND_HANDOVER.md.

## Live local version
http://127.0.0.1:8767/ — server bound to loopback only. Oldstaticdemo/8766 retained. First operator account is not pre-created; user chooses own credentials locally. No default password is supplied.
