# ERP WLB

FastAPI + SQLAlchemy ERP with authenticated CRUD, transactional order stock effects, controlled external imports, and explicit integration operations.

## Local run

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Set a random SECRET_KEY in .env before using real accounts.
alembic upgrade head
python -m erp_fastapi.bootstrap --email owner@example.com
sh start.sh
```

The bootstrap command prompts for a password and creates the admin/operator/viewer roles. For an existing installation, promote the verified owner's existing account using `python -m erp_fastapi.promote_admin --email owner@example.com`. Run these commands on the intended database, never on a temporary copy you intend to discard. Public registration is disabled by default. Admins create accounts through the Users screen or `POST /users/`.

Roles: admin manages users, roles and integrations; operator manages operational records; viewer and unassigned accounts can read operational records and edit their own name/email. Inactive accounts cannot authenticate or use existing tokens. Legacy SHA256 passwords are upgraded to scrypt on successful login. Production requires `APP_ENV=production` and a random `SECRET_KEY` of at least 32 characters. Rotate the old development JWT key when installing this update; users will need to sign in again.

## Railway rollout

1. Back up the actual database and validate a restore before deploying. Inventory, user role assignments and VAT values must be reviewed on the restored copy.
2. Configure a persistent database. Preferred: PostgreSQL using `DATABASE_URL`; `postgres://` is normalized. For SQLite mount a Railway volume at `/data` and set `DATABASE_URL=sqlite:////data/erp.db`. Copy the existing database to that volume while the old service is stopped; do not initialize a blank volume in place of existing customer data.
3. Set `APP_ENV=production`, `SECRET_KEY`, `CORS_ORIGINS=https://erp.wlb.ro`, `ALLOW_REGISTRATION=false`, `AUTO_CREATE_TABLES=false`, `INTEGRATIONS_ENABLED=false`.
4. Promote the owner's existing account with the CLI above. Review and explicitly assign `operator`/`viewer` roles to other existing accounts. Custom legacy role names have read-only access until mapped to a supported role.
5. Build with Dockerfile. `start.sh` runs `alembic upgrade head` then Uvicorn. Railway health checks `/health`, which verifies a database connection. Run schema upgrades with a single deployment instance; do not run concurrent SQLite migrations.
6. Verify sign-in, dashboard, user restrictions, stock and a controlled draft sale on staging. Connect the custom domain only after the service is healthy.
7. Configure integration secrets in the host environment, not in git. Review mappings and fiscal settings, then explicitly enable integrations. No live calls are made by startup, login or order confirmation.

`/health` only checks DB connectivity. This repository cannot confirm host volume settings, backups, Railway environment values, domain/DNS configuration or deployment logs. During development on 2026-10-18, read-only requests to `https://erp.wlb.ro/health` and `/openapi.json` returned HTTP 502 from this environment; this is not enough to identify the infrastructure cause.

## Stock rules

- Draft: no stock movement.
- Confirmed sale / purchase return: reserve the outgoing quantity.
- Completed sale / purchase return: deduct physical quantity and release that order's reservation.
- Completed purchase / sale return: add physical quantity.
- Cancelled open order: release its reservation.
- Finalized/cancelled records are immutable; create a separate return record.
- Only drafts can be deleted. Confirmed lines must be returned to draft before editing.
- Stock effects and order changes commit together. Conditional SQL updates prevent overselling; optimistic order versions reject concurrent updates. Failed orders leave no partial stock movements.
- Manual inventory corrections cannot reduce stock below reserved quantity. Reservations are managed by orders, not edited manually. Every order-generated stock effect is recorded in `stock_movements`.

**Existing orders:** migration does not retrospectively move stock. Existing records receive `workflow_managed=false` and remain read-only until reviewed. Admin-only `POST /orders/{id}/adopt-stock` adopts a draft/confirmed order and applies its reservation once. Review existing manual reservations first to avoid double reservation. Historical completed/cancelled orders remain read-only. Returns are independent documents; matching them to original sales and checking cumulative return limits is not implemented.

Unit prices are net, before VAT; line discount is a percentage. Check imported historical price conventions and VAT rates before fiscal use. Existing defaults are not automatically corrected to any current fiscal rate.

## Integrations

All `/integrations/*` endpoints require admin access. `GET /integrations/status` returns configured/missing setting names without exposing secret values. `GET /integrations/operations` lists outbound write status. No customer data or supplier error bodies are included in public error messages.

Required environment variables:

| Provider | Settings |
| --- | --- |
| eMAG RO | `EMAG_USERNAME`, `EMAG_PASSWORD`; seller API permissions and whitelisted server IP required |
| SmartBill | `SMARTBILL_EMAIL`, `SMARTBILL_TOKEN`, `SMARTBILL_COMPANY_VAT_CODE` |
| Shopify | `SHOPIFY_SHOP` (`store.myshopify.com`), `SHOPIFY_ACCESS_TOKEN`; write_inventory scope |
| Global | `INTEGRATIONS_ENABLED=true` only after configuration and review |

### Import orders

`POST /integrations/orders/import` accepts a reviewed normalized ERP order with `channel`, `external_id`, and `order` (`OrderCreate`). Only draft/confirmed sales are accepted. A unique `(channel, external_id)` constraint makes repeated/concurrent imports return the original ERP order without reserving twice. Channel identifies one configured store/account; multiple accounts per channel are not implemented.

```json
{
  "channel": "emag",
  "external_id": "12345",
  "order": {
    "order_type": "sale",
    "partner_type": "company",
    "partner_id": 1,
    "date": "2026-10-18",
    "status": "draft",
    "items": [{"product_id": 1, "quantity": 2, "unit_price": 15, "vat_percent": 11, "discount_percent": 0}]
  }
}
```

Example IDs/rates above are illustrative; use verified ERP records and fiscal rates. Partner creation/address verification is still an operator responsibility.

`POST /integrations/mappings` accepts `{channel, external_id, product_id, location_id?}`. For eMAG, `external_id` is the seller's offer ID, not the order-line ID. For Shopify it is the inventory-item GID and `location_id` is the location GID. Never assume ERP IDs equal provider IDs.

`POST /integrations/emag/orders/read` reads one paginated page with filters (`currentPage`, `itemsPerPage`, optional status/date range). Filters are sent at the top level, as required by eMAG. It does not acknowledge or alter supplier orders.

`POST /integrations/emag/orders/import` accepts `{external_id, partner_id, partner_type}` and fetches/maps one open eMAG order to a draft sale. Unknown products, vouchers, nonzero shipping, recycling charges and foreign-currency lines are rejected for explicit review; they are not silently discarded. Use the normalized import with reviewed adjustments represented as ERP product/service lines when needed. Import does not synchronize subsequent supplier cancellations; the operator must cancel the ERP order to release reservations.

### SmartBill invoice

`POST /integrations/smartbill/orders/{id}/invoice` accepts `{ "payload": { "seriesName": "...", "client": {"name": "...", "country": "Romania", "address": "..."}, "issueDate": "YYYY-MM-DD" } }`. Supply verified fiscal customer/header data. Product lines, quantities, discounted net prices, VAT percentages, currency RON and issuer are taken from the ERP/configuration. `useStock=false` prevents this action from additionally moving SmartBill inventory. Only confirmed/completed sales are accepted.

The response contains confirmed series/number. A durable unique operation key allows one invoice operation per order. Repeating a succeeded operation returns the original result. After issuing an invoice, do not cancel/change the commercial transaction without reconciling the fiscal document with SmartBill; automated storno/payment reconciliation is not implemented. `GET /integrations/smartbill/orders/{id}/invoice.pdf` downloads the confirmed PDF.

### Publish available stock

`POST /integrations/stock/publish` accepts `{mapping_id, compare_quantity, idempotency_key}` and publishes `quantity - reserved` for that mapped product. Supply a new unique key for each intended stock correction; retry the same operation with the same key. Shopify uses compare-and-set and its required idempotency directive, pinned to API 2026-07. eMAG sends an absolute stock update to warehouse 1; serialize eMAG stock publishing because it has no compare-and-set in this implementation. Do not run multiple stock writers against the same offer.

### Uncertain writes

Timeouts or supplier errors after a write starts produce `uncertain`; the same operation cannot be automatically repeated. Verify the provider's actual state first, then use `POST /integrations/operations/{id}/reconcile` with a descriptive `note` and either `outcome=not_sent` (allows an explicit retry) or `outcome=succeeded` (SmartBill additionally requires confirmed `series` and `number`). A process crash after sending may leave `pending`; an operator must investigate that case in the database before changing it. There is no automatic retry of writes that could duplicate invoices.

### Remaining activation scope

These endpoints are explicit/manual. Background polling, webhook ingestion, Shopify order fetching/product publication, automatic partner/address import, multi-company/multi-warehouse accounting, SmartBill stock synchronization, automatic storno and full shipment/voucher reconciliation are not implemented. They must not be represented as active production integrations. Provider credentials, account mappings, real payload samples and a working host are needed before live validation and expanding automation.

Official API references used: [eMAG 4.5.2](https://marketplace-api.emag.ro/api-doc), [SmartBill OpenAPI](https://api.smartbill.ro/smartbill-api-spec.yaml), [Shopify inventorySetQuantities 2026-07](https://shopify.dev/docs/api/admin-graphql/2026-07/mutations/inventorySetQuantities).

## Verification

```sh
pip install -r requirements-dev.txt
python -m pytest -q
node --check static/js/app.js
```

Tests cover order reservations/completion/cancellation/returns, failed transaction rollback, import deduplication, RBAC/inactive accounts, legacy password upgrade, legacy stock adoption, optimistic concurrency, outbound request contracts, invoice replay/uncertain handling and fresh/legacy migrations. Provider tests mock HTTP; they do not assert live account access. Production/PostgreSQL deployment remains to be verified on the actual host.
