# Replacement implementation follow-up — residual findings only
Reviewer /root/bridgend_review. Read-only current-source review; no source changes or live submissions. Previous P1 public draft-media exposure and homepage new-stock ordering have been fixed in code. Dynamic contact targets/topic selection, source-labelled hours, revision conflict guard, immutable inquiry snapshot, basic category/image lifecycle and pagination are now present. Seven test groups add meaningful recovery/regression coverage. Flask/Jinja architecture remains reasonable. No complete-replacement PASS:1438source photos still unavailable under pending permission.

## P2 — A second normal inquiry in the same session receives409
app/storefront.py contact/enquire/new_enquiry: contact only creates session.submission if absent; successful enquiry never rotates it. Receipt offers Continue browsing. Following that route to another item/contact reuses the already-persistedsubmission_key with a newpayload, so existing.payload_hash mismatch returns409. Only the dedicated Start another enquiry route clears it. Fix per-form nonces with a boundedsession allowlist or equivalent, preserving repeatPOST idempotency while allowing freshforms and multiple tabs. Regression: successfulitemA inquiry → catalogue → itemB → freshform submit succeeds with newID; replayA still returns original receipt without duplicate.

## P2 — Operator cannot preview draft or withdrawn images
Public /media now correctly requires non-draft allowedrights, but templates/admin.html still uses that same URL for every image preview. After adding an image to adraft, even authenticatedoperator sees404; withdrawnmedia also has no usablepreview before restore. Add login-protected adminmedia route checkingimageID/path and serve withno-store; point adminthumbs there. Keep anonymous/public denial intact. Regression: draft upload→adminpreview200/anonymous404; withdrawnimage preview still available toadmin but notpublic.

## P2 — Product next/previous disagrees with newest catalogue
app/storefront.py product() still orderssiblings by CAST(substr(id,7) AS INTEGER), whereas home/catalogue usepublished_order DESC,id DESC. For newrandomBA IDs, entering from newestcatalogue and movingnext can jump unpredictably among sourceitems and reverse the user's expectedsequence. Use the same canonicalordering, ideally preserve category/filtercontext where supported. Regression: create/publish newitems and assert adjacent navigation aligns with defaultnewest listing.

No other newP1 identified in this boundedpass. These residuals should be corrected with targetedtests, then sourcehashrebound. Productimageabsence and productioncutover remain separate knownblockers, not newly introduced codefindings. Tests were inspected, not rerun byreviewer; existing E2E claims remainOwner evidence.

Reviewed manifest SHA256:3304152b44720e55da393ec4e3b21a83c28ce7c95c5101760341a789473dbb0c

## Final targeted verification — all three residual findings resolved
Current source confirms new nonce on every GET/contact, latest20 allowed submission keys, membership validation and existing payload idempotency. New second-inquiry test checks success after a fresh contact GET. Authenticated/admin/media route validatesfilename+DBrecord and uses login_required; admin image template uses this route, public draft-denial remains. Global/admin response header remainsno-store. Tests assert authorisedpreview200 and anonymous302. Productsiblings now usespublished_order DESC,id DESC, matching default catalogue.

Reviewed latest evidence/test-report.txt:7tests OK (Owner execution; reviewer did not rerun). No residualP1/P2 in these three targeted items. This is a focused repair confirmation, not a new full audit or complete-replacementPASS. All1438source images remainpending/unavailable; fullreplacement and productioncutover remainNOT READY.

Verified app/storefront.py SHA256 `450663fc64b2bcd6b8e8c9b9561142091c9f223c5fef5be2a9bab6fdaa14233f`

Verified app/admin.py SHA256 `db21dc6ad7443cdeedd44a86d1d2068d39bed6f1ccfcf1a467fd924c3c505c81`

Verified templates/admin.html SHA256 `19e5544616f145d3a61e5f6676915c2625ba2e11a61cfec84120ba122c385320`

Verified tests/test_app.py SHA256 `e63b7bd8ae50da5df5b9b0a3d44d8fdf0499df29e1ed32ef7903964bf801edcb`

Verified evidence/test-report.txt SHA256 `bd861a4dab7026f7ab08d72920608b01091deea1adbff99053d1aa46995031ea`
