# Local replacement and handover

## What has been implemented
A real locally running Python/Flask application with a durable SQLite database, product/category management, image upload/withdrawal, enquiries, operator access, source import, exports and recovery. Original static demo remains separately preserved. This is no longer a limited static-page product.

## Price and running costs
The user's commercial target is **US$99 as shown / US$199 with a personalised update**. It is a target, not evidence that unrestricted custom development or ongoing service is profitable at that price. Neither price has been sent or accepted by the merchant. To use these prices honestly, deliver this reusable, tested application as a clearly bounded one-time package, explicitly state the included setup/update scope, and obtain the customer's content/media permissions. Do not price this as an incomplete static page while promising full replacement.

- Application software: Flask, Waitress, Python and SQLite require no paid application subscription. Dependencies are pinned in requirements.lock.
- Current local execution: no hosting service was purchased; no email provider or paid API is used.
- Production: needs one persistent Python application instance, persistent writable disk, HTTPS/domain, backup destination and an operator who checks enquiries. Vendor, plan and actual recurring bill are **NOT SELECTED / UNKNOWN**. A disposable filesystem or a static-only hosting plan will lose or fail to support the database.
- Email notifications are not configured. The local inbox is implemented; messages are not sent externally. A production email notification service and delivery test need a separate, authorised configuration. Inbox delivery and email delivery are separate acceptance checks.
- Domain renewal, hosting, storage/backup, email-provider charges, future updates and maintenance are recurring or separate services unless explicitly contracted. No invented monthly figure, silent subscription, or promise of lifetime support.
- Public migration, rights for merchant media, content confirmation, DNS/HTTPS, production staff credentials and merchant acceptance remain separate from local functional testing.

## Run locally
Python3.12. Install the pinned requirements in a project virtual environment. Existing .venv is already ready on this workstation.

```sh
.venv/bin/python tools/import_source.py
.venv/bin/python run.py
```

Visit http://127.0.0.1:8767. Choose your own first operator account at /admin/setup. The setup route works only locally and only before the first account exists. No default credentials are shipped. Keep data/runtime private; it contains customer enquiries and password hashes. Source-only export deliberately excludes operator credentials and session secrets.

Environment: BRIDGEND_DATA chooses an absolute persistent data directory; BRIDGEND_PORT defaults8767. Production must set BRIDGEND_ENV=production and BRIDGEND_HOST to its exact host. This enables Secure cookies and disables web initial setup. Provision the operator on the protected local instance before authorised deployment, use HTTPS reverse proxy, and verify trusted proxy handling for the chosen host. Do not expose setup or serve directly on public HTTP.

## Daily operator workflow
- /admin/products: add/edit stock, select categories, set draft/for-sale/reserved/sold/archive. Publishing moves the piece to the newest position; editing a published piece keeps its publication order.
- /admin/categories: add/rename and hide categories from public filters without deleting relationships.
- Product edit: upload only permitted photos, edit alt text/order, or withdraw an operator upload. Withdrawal is reversible; original media is retained.
- /admin/inquiries: read enquiries, view immutable item context at submission, mark read/responded/closed. Reply using an approved channel; status changes do not send a message.
- /admin/settings: update merchant text, hours and contacts. Changed telephone/address values drive the corresponding actions.
- Re-importing the source preserves operator-edited products. Archived categories and renamed categories are also preserved. Source re-import is manual, not live inventory synchronisation.
- Two conflicting product edits are rejected with submitted values preserved for comparison.

## Backup and recovery

```sh
.venv/bin/python tools/backup.py backup /absolute/runtime /absolute/new-backup-directory
.venv/bin/python tools/backup.py restore /absolute/new-backup-directory /absolute/new-restored-runtime
```

The destination must not exist; live files are never overwritten. Backups contain private enquiries and password hashes and must be protected. SQLite's backup API takes a consistent database snapshot. Media uses immutable content-addressed files, written before database insertion and never deleted by the application: copying all media after the DB snapshot includes every referenced file, and may include harmless later orphan files. Do not externally delete/change media during backup. Manifest hashes are verified before restoration. Session keys are not copied; restored sessions are revoked and the app generates a new key. Test the restored directory separately, then perform an explicitly authorised switch. Never assume that merely having a backup proves recovery.

## Source issues to resolve before claiming complete replacement
1. **1,438 source product photographs remain pending use permission.** Source URLs are recorded; no watermark removal, hotlink or fake item pictures. Existing project policy excludes watermarked imagery. A pending user question requests narrowly scoped permission to retain originals unchanged for this local demo. That would not authorise production or transfer.
2. Hours conflict between public sources. Public text identifies the Atlas schedule and asks visitors to telephone; merchant confirmation is required for definitive current hours.
3. Payment methods for purchases are unverified. Cash buying gold/silver does not establish card acceptance or checkout.
4. Source YouTube video is private; no playable replacement was fabricated. Platform-wide Atlas accounts, advertising, alerts and marketplace discovery remain external services, not merchant-owned functions to reproduce.
5. Source item descriptions/prices/statuses are a dated import, not current stock synchronisation. Merchant must confirm inventory before production.
6. Final media/content rights, production deployment, recipient notification/delivery and operational/customer acceptance are not complete. Do not market this state as live, fully transferable, or client-showable complete replacement.
