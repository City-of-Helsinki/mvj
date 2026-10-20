# Landuse API/UI Implementation Status

Review date: 2026-10-20. Scope: `api/landuse` and `ui/apps/landuse`.

This is an integration backlog, not an implementation change. Findings below are
based on the current request/response mappings and their consumers. Runtime
verification and remaining coverage are documented at the end.

## Confirmed Contract Defects

### Implemented: P1: Saving the summary can silently clear the agreement status

Implemented 2026-10-20: summary form options use backend status codes, save
preserves codes, and read-only display resolves the label. Happy-path adapter
test observed failing before implementation and passing afterward.

- **Read:** `mapAgreementOverviewToSummary` assigns the backend status code
	directly to `tila` (for example, `IN_PROGRESS`).
- **Write:** `getAgreementStatusValue` only recognizes Finnish labels (for
	example, `Vireillä`) and returns an empty string for an existing backend code.
- **Impact:** Open an existing agreement, edit an unrelated summary field and
	save without reselecting the status: the outgoing PATCH clears the status.
	The select options also use labels as values, so the loaded code does not
	match an option.
- **Required:** Use backend enum codes as form values, with separate display
	labels, and add a GET -> edit unrelated field -> PATCH regression test.
- **Evidence:** [UI mapping and save](ui/apps/landuse/src/landUse/api/landUseApi.ts#L308),
	[summary form](ui/apps/landuse/src/landUse/components/tabs/LandUseSummary.tsx#L280),
	[backend enum](api/landuse/models/agreement.py#L8).

## Read/Write Coverage

| Surface | API -> UI | UI -> API | Remaining work |
| --- | --- | --- | --- |
| Agreement creation | Districts and identifiers fetched | POST exists | District code vs database ID; concurrent identifier allocation |
| Agreement list | Partial mapping | N/A | Missing columns, broken phase filtering |
| Summary | GET overview exists | Partial PATCH | Enum round-trip; omitted relationships and collections |
| Parties and billing details | GET exists | Collection PUT exists | Language/country values; role enforcement; error feedback |
| Compensation and sites | GET exists | Two separate PUTs | Lookup IDs not changed by controls; preservation choices; partial saves |
| Collateral requirement | Multiplier and compensation data load | Multiplier PATCH exists | Financial inputs depend on other broken mappings |
| Decisions and conditions | GET exists | Collection PUT exists | Enum display; unsafe deletion of referenced decisions |
| Contracts, amendments and securities | GET exists, mapping incomplete | Not connected | Backend write endpoints and UI mutations absent |
| Payment schedules | GET exists, mapping incomplete | Submit/approve/reject only | No draft creation/editing; approval does not create invoices |
| Invoices and ledger | Partial GET mapping | Not connected in UI | SAP send, invoice provenance, historical recipient and payments |
| Monitoring | Loader returns `null` | No save | Editable prototype with no persistence |

P1 below means data-loss, financial correctness or authorization risk. P2 means
an incomplete workflow or a materially incorrect display. These priorities do
not imply that every finding has been reproduced against a running API.

## Additional Confirmed Defects

### Implemented: P1: Compensation lookup selections do not update the submitted IDs

Implemented 2026-10-20: compensation controls fetch the three lookup endpoints,
retain IDs with display names, and use the selected program's backend discount.
Happy-path lookup and selection tests observed red then green (4 tests pass).

The intended-use and tenure controls change `kayttotarkoitus` and
`hallintamuoto` names, but writes use `kayttotarkoitusId` and
`hallintamuotoIds`. The land-policy control likewise changes
`maapoliittinenOhjelma` and a prototype discount, not
`maapoliittinenOhjelmaId`. New selections therefore save as null/empty, or
preserve the previous IDs. Reload reverses the apparent change.

Fetch `site-intended-uses/`, `site-tenure-types/` and `land-policy-programs/`,
bind controls to IDs, and take default discounts from the selected API record.

Evidence: [site controls](ui/apps/landuse/src/landUse/components/tabs/LandUseCompensations.tsx#L272),
[policy control](ui/apps/landuse/src/landUse/components/tabs/LandUseCompensations.tsx#L526),
[write mapping](ui/apps/landuse/src/landUse/api/landUseApi.ts#L647),
[lookup endpoints](api/landuse/views/lookups.py).

### Implemented: P1: Monitoring edits are discarded by a successful-looking Save

Implemented 2026-10-20 using the documented read-only alternative: monitoring
cannot enter edit mode until persistence exists. Page happy-path test observed
red then green; all 6 page tests pass. Full monitoring persistence remains absent.

`getMonitoring` always returns `null`. The monitoring tab still receives global
edit mode and can change completions, plot divisions and penalty inputs, but
`handleSaveClick` has no monitoring mutation and clears every dirty flag on
success. There is no monitoring persistence model or endpoint in this app.

Implement the persistence contract and save/reload flow, or disable these
controls until it exists. Do not clear unsaved monitoring changes as saved.

Evidence: [null loader](ui/apps/landuse/src/landUse/api/landUseApi.ts#L737),
[save handler](ui/apps/landuse/src/landUse/components/LandUseDetailPage.tsx#L687),
[monitoring form](ui/apps/landuse/src/landUse/components/tabs/LandUseMonitoring.tsx#L69).

### Implemented: P1: Invoice item codes invalidate the paid-compensation deduction

Implemented 2026-10-20: invoice item constants now contain backend codes;
financial comparisons use those codes and rendered fields resolve Finnish
labels. Happy-path financial test observed red then green; 10 tests pass.

Payment-schedule and invoice mappers copy `item_type` unchanged, e.g.
`LAND_USE_COMPENSATION`, `INCREASE` and `INTEREST`. Consumers compare those
values with Finnish strings from the prototype options. Consequently
`calculatePaidMaankayttokorvaus` ignores actual compensation items, overstating
remaining collateral need even for a `PAID` invoice. The interest-kind helper
also fails to recognize backend `INCREASE`/`INTEREST` values.

Use authoritative codes consistently in financial logic and render labels
separately. Add tests using real serializer-shaped invoice and schedule data.

Evidence: [item mappings](ui/apps/landuse/src/landUse/api/landUseApi.ts#L966),
[paid deduction](ui/apps/landuse/src/landUse/components/LandUseDetailPage.tsx#L221),
[interest kind](ui/apps/landuse/src/landUse/components/tabs/LandUsePaymentSchedule.tsx#L278),
[API item enums](api/landuse/models/invoice.py#L39).

### Implemented: P1: Nested API writes do not enforce the affected models' permissions

Implemented 2026-10-20: nested collection writes check
add/change/delete permissions, including affected child records. Happy-path
permission tests observed red then green. Metadata exposes current user
permissions; tab edits, schedule transitions and SAP sending are permission-gated.
Transitions are disabled while form edits are unsaved. Four focused backend and
7 page tests pass. Server checks remain authoritative for individual nested edits.

Agreement actions use `LanduseDjangoModelPermissions` against the agreement
queryset. Thus a PUT to parties/sites/decisions/compensation checks
`change_landuseagreement`, not permissions for the nested records it creates,
updates or deletes. This disagrees with the declared group policy: for example,
`SOPIMUSVALMISTELIJA` can change agreements but has only view permission for
sites, and cannot add/delete parties. The actions do not enforce those limits.

Enforce operation-specific nested permissions, including deletion, and test the
real role matrix. The UI also exposes edit/submit/review controls based on global
edit mode rather than the corresponding permissions; operation endpoints do
check submit/approval/SAP-send permissions, so those controls can lead to 403s.

Evidence: [agreement actions](api/landuse/views/agreement.py#L145),
[group policy and permission class](api/landuse/permissions.py),
[operation permissions](api/landuse/views/operations.py#L20),
[UI action gating](ui/apps/landuse/src/landUse/components/LandUseDetailPage.tsx#L988).

### Implemented: P1: Removing a decision can delete its contracts

Implemented 2026-10-20: collection replacement rejects removal of decisions
referenced by contracts or amendments before mutation. API happy-path protection
test observed red then green; all 6 agreement API tests pass. No migration needed.

The decisions PUT deletes omitted decisions. `ContractDetailsBase.decision`
uses `on_delete=CASCADE`, so removing a decision can delete linked contracts and
their securities/amendments. A payment schedule protecting a contract can
instead block the transaction. Neither behavior is expressed in the UI's
decision deletion workflow. Decide whether references should be protected or
cleared explicitly, and test deletion with linked contracts and schedules.

Evidence: [replacement deletion](api/landuse/views/agreement.py#L319),
[contract decision relation](api/landuse/models/contract.py#L37).

### Implemented: P2: Party language and country options do not match the API contract

Implemented 2026-10-20: both party form types fetch language/country codes from
UI metadata; metadata includes the complete django-countries catalog. Party and
invoice-recipient writes use the same country choices. Red/green metadata tests
pass; 8 focused backend and 9 focused UI tests pass.

The UI sends `suomi`, `ruotsi`, `englanti`; backend language choices are `fi`,
`sv`, `en`. Selecting a language therefore makes the parties PUT invalid,
including for a separate invoice recipient. Countries use `suomi`, `ruotsi`,
`norja` instead of CountryField country codes such as `FI`, `SE`, `NO`; the
agreement-party write serializer derives validation from that model field.
Existing API codes also have no matching prototype options.

Use metadata language codes and a country-code option source. Confirm identical
country validation for party and invoice-recipient serializers, since the latter
explicitly overrides country with a plain CharField.

Evidence: [prototype options](ui/apps/landuse/src/landUse/options.ts),
[party write mapping](ui/apps/landuse/src/landUse/api/landUseApi.ts#L521),
[model fields](api/landuse/models/party.py#L43),
[configured languages](api/mvj/settings.py#L207),
[serializers](api/landuse/serializers/agreement.py#L161).

### Implemented: P2: Several summary controls are never included in Save

Implemented 2026-10-20: summary saves addresses/preparers with stable IDs and
model permission checks, retains plan/signatory IDs, fetches real signatory and
preparer choices, and reloads canonical overview data after PATCH. Happy paths
observed red then green; 9 backend and 10 UI tests pass.

Addresses, preparers, authorized signatory and selected detailed plan are loaded
or editable, but `updateSummary` sends none of them. It returns the submitted
form values instead of rereading the server, hiding the loss until reload.
Addresses/preparers are read-only nested serializer fields with no write action.
Detailed plan and authorized signatory can be PATCHed as foreign-key IDs, but the
form holds a plan number and signatory name. Preparers still offer
`valmistelija1`/`valmistelija2`/`valmistelija3`, and signatory uses decision-maker
choices rather than `authorized-signatories/` records. Loaded preparer names are
discarded in favor of their IDs.

Add writable collection contracts and real user options; retain relationship
IDs; include all supported edits and reconcile with the canonical response.

Evidence: [summary mapping/save](ui/apps/landuse/src/landUse/api/landUseApi.ts#L351),
[summary controls](ui/apps/landuse/src/landUse/components/tabs/LandUseSummary.tsx#L410),
[prototype preparers](ui/apps/landuse/src/landUse/components/tabs/LandUseSummary.tsx#L774),
[overview serializer](api/landuse/serializers/agreement.py#L132).

### Implemented: P2: List filtering and advertised search fields are incomplete

Implemented 2026-10-20: list responses include party names, plan number, sites
and promotion-area state; the UI maps those fields and filters by status codes
with labeled display. Red/green happy paths pass (8 API and 5 adapter tests).

The list gets status codes but filters against Finnish labels, so selecting a
phase excludes matching agreements. Party, plan number and site are hardcoded
to empty strings, making those columns and the advertised party/plan search
unusable. `projectArea` reads `is_promotion_area`, which the list serializer does
not return. Extend the list response and align filters with codes; do not imply
that absent data has been searched.

Evidence: [list mapping](ui/apps/landuse/src/landUse/api/landUseApi.ts#L410),
[client filtering](ui/apps/landuse/src/landUse/components/LandUseListPage.tsx#L185),
[list serializer](api/landuse/serializers/agreement.py#L88).

### Implemented: P2: Collateral types disappear and relationship displays use the wrong keys

Implemented 2026-10-20: contract/collateral labels resolve from metadata, record
IDs survive mapping, party controls use IDs with named read-only display, and
decision controls resolve actual decision records. Happy path observed red then
green; 17 adapter/financial tests pass.

`getLabelForCode(LAND_USE_GUARANTEE_TYPES, "MORTGAGE_DEED")` returns undefined:
the UI object keys are `PANTTIKIRJA`, `RAHAVAKUUS`, etc. This loses the type used
to select a collateral-specific form. Document category, target and contract type
also pass through as raw backend codes. Collateral parties are mapped to string
IDs, but contract party options use names as values; contract decisions are IDs,
while the prototype decision dropdown offers decision *types*, not records.
Contract, amendment and collateral IDs are discarded by the read mapper, which
must be addressed before adding writes.

Evidence: [contract mapping](ui/apps/landuse/src/landUse/api/landUseApi.ts#L804),
[party options](ui/apps/landuse/src/landUse/components/tabs/LandUseContracts.tsx#L151),
[decision control](ui/apps/landuse/src/landUse/components/tabs/LandUseContracts.tsx#L409),
[backend collateral enums](api/landuse/models/contract.py#L97).

### Implemented: P2: Invoice type and historical billing details are lost in the read mapping

Implemented 2026-10-20: billing retains invoice/source IDs, historical recipients
and ledger entries, resolves invoice type, displays snapshot names/details and
payment history, and protects source-generated invoice content. Happy path
observed red then green; 18 adapter/financial tests pass.

Invoice type has the same key mismatch: `LAND_USE_COMPENSATION` and `PENALTY`
are looked up in an object keyed by `MAANKAYTTOKORVAUS` and `SAKKO`, yielding
undefined. `getBilling` drops invoice IDs, installment provenance,
`recipient_snapshot` and `payments`; billing instead resolves recipient details
from the current party. Changing a party can therefore change what an old
invoice appears to have contained. Payment dates, amounts and filing codes
already returned by the backend are not available in the mapped billing data.

Retain invoice identity/provenance, display historical recipient data from the
snapshot, and expose ledger entries. Source-generated invoice edit protection
also needs the retained provenance when editing is enabled.

Evidence: [billing mapping](ui/apps/landuse/src/landUse/api/landUseApi.ts#L979),
[billing recipient display](ui/apps/landuse/src/landUse/components/tabs/LandUseBilling.tsx#L178),
[invoice serializer](api/landuse/serializers/agreement.py#L685).

### Implemented: P2: Preservation choices, empty years and date formats disagree

Implemented 2026-10-20: optional years clear to null; preservation supports
blank/SR1/SR2/SR3; date-only response fields format for Finnish controls; day
counts accept ISO and Finnish dates using UTC arithmetic without Temporal.
Happy path observed red then green; 16 adapter/financial tests pass.

- Preservation offers `-`, `SR1`, `SR2`, but backend allows null/blank and
	`SR1`/`SR2`/`SR3`. Choosing `-` sends an invalid choice, and `SR3` is absent.
- `getOptionalYear("")` returns `0`, not null, so clearing a year writes zero.
- API dates are copied as ISO strings into Finnish DateInputs. The schedule
	day-count helper only parses `DD.MM.YYYY`, so loaded ISO calculation periods
	produce zero days. Normalize at the adapter boundary or make consumers accept
	ISO; verify the DateInput display/edit behavior in a browser.
- The date helper references global `Temporal` without a declared type or
	polyfill dependency; typechecking fails and runtime support is browser-dependent.

Evidence: [options](ui/apps/landuse/src/landUse/options.ts),
[year helper](ui/apps/landuse/src/landUse/api/landUseApi.ts#L304),
[preservation model](api/landuse/models/site.py#L31),
[date parser](ui/apps/landuse/src/landUse/utils/date.ts),
[day-count consumer](ui/apps/landuse/src/landUse/components/tabs/LandUsePaymentSchedule.tsx#L807).

### Implemented: P2: Agreement identifiers use district database IDs and race on allocation

Implemented 2026-10-20: creation allocates identifiers in an atomic backend
operation under a district lock using its public code. The UI sends municipality
and district IDs without generating a sequence. Red/green tests pass (9 API and
9 adapter tests). Allocation assumes district codes are unique in lookup data.

The district dropdown value is its database PK. That value is used both for the
foreign key and the human identifier's district segment, although the lookup has
a separate `identifier` code. Those values need not match; the district fixture
does not even fix primary keys. Sequence allocation fetches existing identifiers
and computes max+1 in the browser, so concurrent creates can choose the same
identifier and one fails the unique constraint. Move allocation to the backend
and distinguish district PK from district code.

Evidence: [district options/create](ui/apps/landuse/src/landUse/components/LandUseListPage.tsx#L249),
[creation adapter](ui/apps/landuse/src/landUse/api/landUseApi.ts#L427),
[identifier helper](ui/apps/landuse/src/landUse/utils/landUseIdentifier.ts),
[district fixture](api/landuse/fixtures/districts.json).

## Missing Workflow Implementations

### Implemented: P1: Approval does not materialize invoice drafts

Implemented 2026-10-20: approval locks the schedule and atomically creates
source-linked invoice drafts, copied items/totals and recipient snapshots.
Existing source links are reused; non-pending repeated approvals are rejected.
Happy path observed red then green; 7 schedule/operation tests pass.

The approve endpoint calls `PaymentSchedule.approve`, which only saves status
and rejection reason. No landuse signal or service creates invoices/items from
installments or fills `source_payment_schedule_installment`. Refreshing billing
after approval therefore does not create the expected invoices. Existing
operation tests create an unrelated invoice before approval and only assert the
schedule status.

Implement atomic, duplicate-safe materialization with recipient snapshots and
source links. Verify the intended business trigger if approval is not meant to
perform this step; another explicit operation is currently absent.

Evidence: [approval operation](api/landuse/views/operations.py#L60),
[model transition](api/landuse/models/payment_schedule.py#L133),
[operation test](api/landuse/tests/test_operation_api.py#L27),
[invoice source relation](api/landuse/models/invoice.py#L61).

### Implemented: P2: Contracts and payment-schedule drafts have no write path

Implemented 2026-10-20: agreement endpoints accept contract/amendment/collateral
and draft/rejected schedule writes, validate ownership and nested permissions,
and preserve record IDs. UI editing/saving is connected, with metadata-backed
contract code conversion. Corrected collateral reverse relation sources in the
existing read serializers/prefetches. Red/green happy paths pass; 18 focused API
tests and 17 adapter/page tests pass.

Contracts/securities/amendments have a GET-only agreement action. Schedules have
GET-only collection/detail endpoints plus transitions. The page explicitly sets
both tabs to read-only and has no corresponding save mutations. Users cannot
create the contract and draft installments needed to begin the workflow, or
correct a rejected schedule. These are missing features, not failing PUT calls.

Evidence: [read-only actions](api/landuse/views/agreement.py#L347),
[schedule viewset](api/landuse/views/operations.py#L46),
[tab wiring](ui/apps/landuse/src/landUse/components/LandUseDetailPage.tsx#L988).

### Implemented: P2: SAP sending and invoice editing remain disconnected from the UI

Implemented 2026-10-20: persisted invoice drafts can call the backend SAP send
operation and refresh canonical billing data. Removed simulated status, amount
and invoice-number changes. Invoice content remains read-only; drafts originate
from approved schedules. Red/green adapter happy path passes; 22 focused tests
pass. Actual external SAP delivery is not exercised in unit tests.

The backend exposes `POST invoices/{id}/send-to-sap/`, but the UI has no adapter
or callback for it. Billing is explicitly read-only. Its dormant prototype
status button only changes form state and fabricates an invoice number with
`Date.now()`; it is not a SAP integration. Simply re-enabling edit mode would
also expose local invoice creation/deletion without persistence. Define the
supported invoice operations, wire real mutations, and remove simulated status
changes rather than enabling them.

Evidence: [SAP action](api/landuse/views/operations.py#L94),
[prototype status action](ui/apps/landuse/src/landUse/components/tabs/LandUseBilling.tsx#L579),
[read-only billing wiring](ui/apps/landuse/src/landUse/components/LandUseDetailPage.tsx#L1068).

## Cross-Cutting Integration Work

- **Implemented: Authoritative metadata:** Live summary, decision, party,
  preservation, contract and collateral selectors now consume metadata and
  database-backed compensation options use lookup endpoints. Shared code constants
  and legacy fixtures remain separate from live choices. Happy-path metadata
  option test observed red then green; 25 focused tests pass.

  Original task: Consume `landuse/ui-metadata/` instead of maintaining
	parallel enum translations. Its payload already covers statuses, party roles,
	decision types, contract/collateral types, languages and preservation choices.
	Database-backed options need the separate lookup endpoints. Do not treat all
	of [options.ts](ui/apps/landuse/src/landUse/options.ts) as one removable mock:
	it also contains shared form types/constants. The prototype plan array is not
	the active plan source; `getAsemakaavat` already fetches the API.
	Evidence: [metadata view](api/landuse/views/ui_metadata.py),
	[lookup viewsets](api/landuse/views/lookups.py).

- **Implemented: Errors and partial saves:** Detail/list/create and financial
	actions expose API validation errors; successfully saved tabs are reconciled
	separately, failed tabs retain edits for retry. Compensation/sites save in one
	atomic document operation. Red/green happy paths pass (12 API / 21 UI tests).
	Original task: Save catches only log to the console; list/create
	and non-404 detail failures have no meaningful user-facing error state. Nested
	validation, protected party deletion and denied operations need actionable
	feedback. Compensation and sites save concurrently in separate transactions,
	and tabs save sequentially, so failures can leave only part of an edit saved.
	Preserve dirty state per failed operation and reconcile successful results, or
	provide an atomic aggregate write contract where required.
	Evidence: [save orchestration](ui/apps/landuse/src/landUse/components/LandUseDetailPage.tsx#L687),
	[compensation writes](ui/apps/landuse/src/landUse/api/landUseApi.ts#L647),
	[protected party relations](api/landuse/models/payment_schedule.py#L54).

- **Implemented: Stable relationships and cache refresh:** Schedule writes retain
	party/contract IDs, loaded relationship positions resolve against current IDs,
	invoice history uses recipient snapshots, and dependent queries refresh after
	saves. Financial transitions are disabled while edits are unsaved. Happy-path
	ID resolution test observed red then green; 22 adapter/page tests pass.
	Original task: Schedules/invoices reference party
	array indexes in forms; their adapters derive indexes from separate API calls.
	Updating/removing parties does not refresh those dependent queries. Use stable
	IDs for relationships and invalidate dependent data after mutations to avoid
	showing a different party at a retained index. Also test unsaved party edits
	before submitting/reviewing schedules, since actions operate on persisted data.
	Evidence: [index mapping](ui/apps/landuse/src/landUse/api/landUseApi.ts#L887),
	[party mutation](ui/apps/landuse/src/landUse/components/LandUseDetailPage.tsx#L650).

## Verification And Acceptance

Executed during this review:

- Focused Node assertions against the current UI source confirmed the status
	round-trip loss, undefined collateral/invoice type lookups, failed compensation
	item comparison and empty-year-to-zero conversion.
- `cd ui && yarn vitest run apps/landuse/src/landUse/components/__tests__/LandUseDetailPage.spec.tsx apps/landuse/src/landUse/components/tabs/__tests__/LandUseCompensations.spec.ts apps/landuse/src/landUse/components/tabs/__tests__/LandUseInvoiceReview.spec.ts`:
	**3 files / 15 tests passed**. Non-fatal output included missing leasing
	Leaflet copy assets, stylesheet parsing and jsdom `scrollTo` warnings.
- `cd ui && yarn tsc --noEmit -p apps/landuse/tsconfig.json`:
	**failed with 12 errors across 5 files**. Missing summary `identifier` in empty
	values and seed factories; stale mocks for nonexistent `updateMonitoring`,
	`updateContracts`, `updatePaymentSchedule`, `updateBilling`; test typing errors;
	undeclared `Temporal`.

The existing page tests mock the API module, so passing tests do not establish
serializer/adapter compatibility. Backend behavior above was traced through
models, serializers, views, permissions and nearby tests, not reproduced via
authenticated requests. No Python tests, migrations, live SAP calls or browser
end-to-end flows were run; application source was not changed.

Recommended completion gates:

1. Repair the data-loss/financial/authorization findings first; adopt API enum
	 codes and lookup IDs throughout forms and adapters.
2. Add adapter contract tests using backend-shaped payloads and assert exact
	 outgoing requests, including untouched values and cleared fields.
3. Add backend role and deletion tests for nested writes, plus approval invoice
	 materialization tests with repeated/concurrent attempts.
4. Add missing writes and verify create -> edit -> save -> reload for each tab,
	 then draft -> submit -> reject/edit/resubmit -> approve -> invoice -> SAP send.
5. Verify historical invoice display after party edits, ledger rendering, partial
	 failure recovery and action permissions with representative user roles.
6. Restore a clean landuse TypeScript check and run the relevant backend tests
	 and browser workflows before considering the bidirectional contract complete.
