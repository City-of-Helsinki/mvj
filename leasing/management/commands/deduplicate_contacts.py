import json
import logging
import sys
from collections import defaultdict
from typing import TypedDict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import QuerySet
from safedelete import HARD_DELETE

from credit_integration.models import CreditDecision
from leasing.models.contact import Contact
from leasing.models.invoice import Invoice
from leasing.models.lease import Lease
from leasing.models.tenant import TenantContact

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)


class _DuplicateKey(TypedDict):
    name: str
    business_id: str


class _DuplicateDetail(TypedDict):
    id: int
    name: str | None
    first_name: str | None
    last_name: str | None
    business_id: str | None
    deleted: str | None
    created_at: str | None


class _TenantContactRef(TypedDict):
    tenant_contact_id: int
    contact_id: int
    tenant_id: int


class _CreditDecisionRef(TypedDict):
    credit_decision_id: int
    customer_id: int | None


class _InvoiceRef(TypedDict):
    invoice_id: int
    recipient_id: int


class _References(TypedDict):
    tenant_contacts: list[_TenantContactRef]
    credit_decisions: list[_CreditDecisionRef]
    invoices: list[_InvoiceRef]


class _SetInfo(TypedDict):
    key: _DuplicateKey
    original_id: int
    original_deleted: bool
    duplicate_ids: list[int]
    duplicates_detail: list[_DuplicateDetail]
    references: _References


class _InvoiceEntry(TypedDict):
    key: _DuplicateKey
    original_id: int
    total_invoices_to_change: int
    invoices_per_duplicate_contact: dict[int, int]


class Command(BaseCommand):
    help = "Deduplicate contacts that have been duplicated due to a bug when copying a lease to a new service unit."

    # Hardcoded scope: only service unit 2, only duplicates created on 2025-11-27.
    # These are intentionally not command-line parameters to prevent accidental misuse.
    TARGET_SERVICE_UNIT_ID = 2
    TARGET_DATE = "2025-11-27"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="deduplicate_contacts_report.json",
            help="Output file for the deduplication report (default: deduplicate_contacts_report.json)",
        )
        parser.add_argument(
            "--invoice-output",
            default="deduplicate_contacts_invoices.json",
            help="Output file for invoice statistics (default: deduplicate_contacts_invoices.json)",
        )
        parser.add_argument(
            "--replace-references",
            action="store_true",
            default=False,
            help="Actually replace references to duplicates with the original contact. "
            "Without this flag, only analysis is performed.",
        )
        parser.add_argument(
            "--delete-duplicates",
            action="store_true",
            default=False,
            help="Delete duplicate contacts after replacing references. "
            "Requires --replace-references.",
        )

    def handle(self, *args, **options):
        service_unit_id = self.TARGET_SERVICE_UNIT_ID
        target_date = self.TARGET_DATE
        output_file = options["output"]
        invoice_output_file = options["invoice_output"]
        do_replace = options["replace_references"]
        do_delete = options["delete_duplicates"]

        if do_delete and not do_replace:
            logger.error("--delete-duplicates requires --replace-references")
            return

        leases = Lease.objects.filter(service_unit_id=service_unit_id)
        logger.info(
            "Found %d leases for service unit %d", leases.count(), service_unit_id
        )

        contacts_qs = Contact.all_objects.filter(
            service_unit_id=service_unit_id,
            created_at__date=target_date,
        )
        logger.info(
            "Found %d contacts (including archived) created on %s in service unit %d",
            contacts_qs.count(),
            target_date,
            service_unit_id,
        )

        duplicate_sets = self._find_duplicate_sets(contacts_qs)
        logger.info(
            "Found %d duplicate sets (%d contacts total)",
            len(duplicate_sets),
            sum(len(v) for v in duplicate_sets.values()),
        )

        report, invoice_report = self._build_report(duplicate_sets)
        self._write_reports(
            report, invoice_report, service_unit_id, output_file, invoice_output_file
        )

        if not do_replace:
            logger.warning(
                "Dry run complete. Use --replace-references to actually replace references."
            )
            return

        self._replace_references(report)

        if do_delete:
            self._delete_duplicate_contacts(report)

    def _find_duplicate_sets(
        self, contacts_qs: QuerySet[Contact]
    ) -> dict[tuple[str, str], list[Contact]]:
        """Group contacts by (name, business_id) and return sets with more than one contact.

        Contacts where both name and business_id are absent are skipped.
        """
        duplicates_map: dict[tuple[str, str], list[Contact]] = defaultdict(list)
        for contact in contacts_qs:
            if not contact.name and not contact.business_id:
                continue
            key = (contact.name or "", contact.business_id or "")
            duplicates_map[key].append(contact)

        return {
            key: contacts
            for key, contacts in duplicates_map.items()
            if len(contacts) > 1
        }

    def _build_report(
        self, duplicate_sets: dict[tuple[str, str], list[Contact]]
    ) -> tuple[list[_SetInfo], list[_InvoiceEntry]]:
        """Build the full report and invoice report from the duplicate sets."""
        report = []
        invoice_report = []

        for key, contacts in duplicate_sets.items():
            set_info, invoice_entry = self._build_set_report(key, contacts)
            report.append(set_info)
            if invoice_entry:
                invoice_report.append(invoice_entry)

        return report, invoice_report

    def _find_original(self, contacts: list[Contact]) -> Contact:
        """Return the contact to keep: the oldest one, i.e. one with the lowest primary key."""
        return min(contacts, key=lambda c: c.pk)

    def _build_set_report(
        self, key: tuple[str, str], contacts: list[Contact]
    ) -> tuple[_SetInfo, _InvoiceEntry | None]:
        """Build the report entry for one duplicate set.

        The original contact is the one with the lowest id.
        """
        original = self._find_original(contacts)
        duplicates = [c for c in contacts if c.pk != original.pk]
        duplicate_ids = [c.pk for c in duplicates]

        set_info: _SetInfo = {
            "key": {"name": key[0], "business_id": key[1]},
            "original_id": original.pk,
            "original_deleted": original.deleted is not None,
            "duplicate_ids": duplicate_ids,
            "duplicates_detail": [
                {
                    "id": dup.pk,
                    "name": dup.name,
                    "first_name": dup.first_name,
                    "last_name": dup.last_name,
                    "business_id": dup.business_id,
                    "deleted": dup.deleted.isoformat() if dup.deleted else None,
                    "created_at": (
                        dup.created_at.isoformat() if dup.created_at else None
                    ),
                }
                for dup in duplicates
            ],
            "references": {
                "tenant_contacts": [
                    {
                        "tenant_contact_id": tc.pk,
                        "contact_id": tc.contact.pk,
                        "tenant_id": tc.tenant.pk,
                    }
                    for tc in TenantContact.objects.filter(contact_id__in=duplicate_ids)
                ],
                "credit_decisions": [
                    {
                        "credit_decision_id": cd.pk,
                        "customer_id": cd.customer.pk,
                    }
                    for cd in CreditDecision.objects.filter(
                        customer_id__in=duplicate_ids
                    )
                ],
                "invoices": [
                    {
                        "invoice_id": inv.pk,
                        "recipient_id": inv.recipient.pk,
                    }
                    for inv in Invoice.objects.filter(recipient_id__in=duplicate_ids)
                ],
            },
        }

        invoice_stats = defaultdict(int)
        for inv_ref in set_info["references"]["invoices"]:
            invoice_stats[inv_ref["recipient_id"]] += 1

        invoice_entry: _InvoiceEntry | None = None
        if invoice_stats:
            invoice_entry = {
                "key": {"name": key[0], "business_id": key[1]},
                "original_id": original.pk,
                "total_invoices_to_change": sum(invoice_stats.values()),
                "invoices_per_duplicate_contact": dict(invoice_stats),
            }

        return set_info, invoice_entry

    def _write_reports(
        self,
        report: list[_SetInfo],
        invoice_report: list[_InvoiceEntry],
        service_unit_id: int,
        output_file: str,
        invoice_output_file: str,
    ) -> None:
        """Write the duplicate-set report and invoice statistics to JSON files."""
        report_output = {
            "service_unit_id": service_unit_id,
            "total_duplicate_sets": len(report),
            "total_duplicate_contacts": sum(len(s["duplicate_ids"]) for s in report),
            "duplicate_sets": report,
        }
        with open(output_file, "w") as f:
            json.dump(report_output, f, indent=2, default=str)
        logger.info("Report written to %s", output_file)

        invoice_output = {
            "service_unit_id": service_unit_id,
            "total_invoices_to_change": sum(
                item["total_invoices_to_change"] for item in invoice_report
            ),
            "sets_with_invoices": len(invoice_report),
            "details": invoice_report,
        }
        with open(invoice_output_file, "w") as f:
            json.dump(invoice_output, f, indent=2, default=str)
        logger.info("Invoice statistics written to %s", invoice_output_file)

    def _replace_references(self, report: list[_SetInfo]) -> None:
        """Replace all FK references from duplicate contacts with the original contact."""
        logger.info("Replacing references to duplicates...")

        with transaction.atomic():
            for set_info in report:
                original_id = set_info["original_id"]
                duplicate_ids = set_info["duplicate_ids"]

                tc_updated = TenantContact.objects.filter(
                    contact_id__in=duplicate_ids
                ).update(contact_id=original_id)
                if tc_updated:
                    logger.info(
                        "Updated %d TenantContact(s) for original contact %d",
                        tc_updated,
                        original_id,
                    )

                cd_updated = CreditDecision.objects.filter(
                    customer_id__in=duplicate_ids
                ).update(customer_id=original_id)
                if cd_updated:
                    logger.info(
                        "Updated %d CreditDecision(s) for original contact %d",
                        cd_updated,
                        original_id,
                    )

                inv_updated = Invoice.objects.filter(
                    recipient_id__in=duplicate_ids
                ).update(recipient_id=original_id)
                if inv_updated:
                    logger.info(
                        "Updated %d Invoice(s) for original contact %d",
                        inv_updated,
                        original_id,
                    )

        logger.info("References replaced.")

    def _delete_duplicate_contacts(self, report: list[_SetInfo]) -> None:
        """Hard-delete all duplicate contacts, bypassing safedelete soft-deletion."""
        logger.info("Deleting duplicate contacts...")
        deleted_count = 0
        for set_info in report:
            for dup_id in set_info["duplicate_ids"]:
                contact = Contact.all_objects.get(id=dup_id)
                contact.delete(force_policy=HARD_DELETE)
                deleted_count += 1
        logger.info("Deleted %d duplicate contact(s).", deleted_count)
