import csv
import logging
import sys
from datetime import datetime
from typing import TypedDict

from auditlog.models import LogEntry, LogEntryManager
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from leasing.enums import DecisionTypeKind
from leasing.models import Comment, Lease, ServiceUnit
from leasing.models.comment import CommentTopic
from leasing.models.contact import Contact
from leasing.models.contract import Collateral, Contract
from leasing.models.decision import Decision, DecisionMaker, DecisionType
from leasing.models.lease import IntendedUse
from leasing.models.receivable_type import ReceivableType
from leasing.models.rent import Rent
from leasing.models.tenant import Tenant, TenantContact
from users.models import User

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)


REQUIRED_HEADERS = [
    "lease_identifier",
    "target_service_unit_name",
    "target_lessor_name",
    "target_receivable_type_name",
    "target_intended_use_name",
    "transferrer_email",
    "decision_reference_number",
    "decision_maker_name",
    "decision_date",
    "decision_section",
]

"""Example CSV content:   # noqa: E501
lease_identifier,target_service_unit_name,target_lessor_name,target_receivable_type_name,target_intended_use_name,transferrer_email,decision_reference_number,decision_maker_name,decision_date,decision_section
A1234-123,Alueiden käyttö ja valvonta,Alueiden käyttö ja valvonta,Pysäköinti,Sähköauton latauspaikka,first.last@example.com,HEL 2025-0123456,Alueidenkäyttöpäällikkö,2025-03-30,123
"""


class TransferRow(TypedDict):
    lease_identifier: str
    target_service_unit_name: str
    target_lessor_name: str
    target_receivable_type_name: str
    target_intended_use_name: str
    transferrer_email: str
    decision_reference_number: str
    decision_maker_name: str
    decision_date: str
    decision_section: str


class Command(BaseCommand):
    help = "Transfer leases from one service unit to another"

    def add_arguments(self, parser):
        parser.add_argument("csv", type=str, help="Path to CSV file")

    def handle(self, *args, **options):
        with open(options["csv"], "r") as file:
            reader: list[TransferRow] = csv.DictReader(file, delimiter=",")

            self.validate_headers(reader.fieldnames)

            confirm = input("\nProceed with transfer? [y/N]: ")
            if confirm.lower() != "y":
                logger.info("Transfer cancelled.")
                return

            try:
                with transaction.atomic():
                    for i, row in enumerate(reader, start=2):
                        (
                            lease,
                            target_service_unit,
                            target_lessor,
                            target_receivable_type,
                            target_intended_use,
                            decision_maker,
                            transferrer_email,
                        ) = self.get_target_objects_from_row(row, i)
                        self.validate_target_objects(
                            lease,
                            target_service_unit,
                            target_lessor,
                            target_receivable_type,
                            target_intended_use,
                            i,
                        )
                        (
                            decision_reference_number,
                            decision_date,
                            decision_section,
                        ) = self.get_decision_info_from_row(row, i)

                        logger.info(
                            f"{i}: Transferring {lease.identifier} to service unit {target_service_unit}"
                        )
                        self.perform_single_transfer(
                            lease,
                            target_service_unit,
                            target_lessor,
                            target_receivable_type,
                            target_intended_use,
                            transferrer_email,
                            decision_reference_number,
                            decision_maker,
                            decision_date,
                            decision_section,
                        )

            except CommandError:
                raise
            except Exception as e:
                raise CommandError(f"Transfer failed: {str(e)}")

    def validate_headers(self, fieldnames):
        if len(fieldnames) != len(REQUIRED_HEADERS):
            raise CommandError(
                f"Must provide {len(REQUIRED_HEADERS)} headers, provided: {len(fieldnames)}"
            )
        for i, (expected, actual) in enumerate(zip(REQUIRED_HEADERS, fieldnames)):
            if expected != actual:
                raise CommandError(
                    f"CSV column {i+1} must be '{expected}', but found '{actual}'. "
                    f"Expected exact order: {REQUIRED_HEADERS}"
                )
        return

    def get_target_objects_from_row(self, row: TransferRow, row_number=None):
        (
            lease_identifier,
            target_service_unit_name,
            target_lessor_name,
            target_receivable_type_name,
            target_intended_use_name,
            decision_maker_name,
            transferrer_email,
        ) = (
            row["lease_identifier"],
            row["target_service_unit_name"],
            row["target_lessor_name"],
            row["target_receivable_type_name"],
            row["target_intended_use_name"],
            row["decision_maker_name"],
            row["transferrer_email"],
        )
        try:
            lease = Lease.objects.get(identifier__identifier=lease_identifier)
            target_service_unit = ServiceUnit.objects.get(name=target_service_unit_name)
            target_lessor = Contact.objects.get(
                name=target_lessor_name,
                is_lessor=True,
                service_unit=target_service_unit,
            )
            target_receivable_type = ReceivableType.objects.get(
                name=target_receivable_type_name,
                service_unit=target_service_unit,
                is_active=True,
            )
            target_intended_use = IntendedUse.objects.get(
                name=target_intended_use_name,
                service_unit=target_service_unit,
                is_active=True,
            )
            decision_maker = DecisionMaker.objects.get(name=decision_maker_name)
            transferrer_user = User.objects.get(email=transferrer_email)
        except Lease.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: Lease {lease_identifier} does not exist"
            )
        except ServiceUnit.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: Service unit {target_service_unit_name} does not exist"
            )
        except Contact.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: Lessor {target_lessor_name} does not exist for service unit {target_service_unit}"
            )
        except ReceivableType.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: Receivable type {target_receivable_type_name} does not exist for service unit "
                f"{target_service_unit}"
            )
        except IntendedUse.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: Intended use {target_intended_use_name} does not exist for service unit "
                f"{target_service_unit}"
            )
        except DecisionMaker.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: Decision maker {decision_maker_name} does not exist"
            )
        except User.DoesNotExist:
            raise CommandError(
                f"Row {row_number}: User with email {row['transferrer_email']} does not exist"
            )

        return (
            lease,
            target_service_unit,
            target_lessor,
            target_receivable_type,
            target_intended_use,
            decision_maker,
            transferrer_user,
        )

    def validate_target_objects(
        self,
        lease: Lease,
        target_service_unit: ServiceUnit,
        target_lessor: Contact,
        target_receivable_type: ReceivableType,
        target_intended_use: IntendedUse,
        row_number=None,
    ):
        if lease.service_unit == target_service_unit:
            raise CommandError(
                f"Row {row_number}: Lease {lease.identifier} is already assigned to {target_service_unit}"
            )
        if target_lessor.service_unit != target_service_unit:
            raise CommandError(
                f"Row {row_number}: Lessor {target_lessor} does not belong to service unit {target_service_unit}"
            )
        if target_receivable_type.service_unit != target_service_unit:
            raise CommandError(
                f"Row {row_number}: Receivable type {target_receivable_type} does not belong to service unit "
                f"{target_service_unit}"
            )
        if target_intended_use.service_unit != target_service_unit:
            raise CommandError(
                f"Row {row_number}: Intended use {target_intended_use} does not belong to service unit "
                f"{target_service_unit}"
            )
        return

    def get_decision_info_from_row(self, row: TransferRow, row_number=None):
        (
            decision_reference_number,
            decision_date,
            decision_section,
        ) = (
            row["decision_reference_number"],
            row["decision_date"],
            row["decision_section"],
        )
        if not all(
            [
                decision_reference_number,
                decision_date,
                decision_section,
            ]
        ):
            raise CommandError(
                f"Row {row_number}: All decision fields must be provided (reference number, date, section)"
            )

        try:
            decision_date_parsed = timezone.datetime.strptime(
                decision_date, "%Y-%m-%d"
            ).date()
        except ValueError:
            raise CommandError(
                f"Row {row_number}: Decision date '{decision_date}' is not in the format YYYY-MM-DD"
            )
        if not decision_reference_number.startswith("HEL"):
            raise CommandError(
                f"Row {row_number}: Decision reference number '{decision_reference_number}' must start with 'HEL'"
            )
        if not decision_section.isdigit():
            raise CommandError(
                f"Row {row_number}: Decision section '{decision_section}' must contain only numbers"
            )

        return (
            decision_reference_number,
            decision_date_parsed,
            decision_section,
        )

    def perform_single_transfer(
        self,
        lease: Lease,
        target_service_unit: ServiceUnit,
        lessor: Contact,
        receivable_type: ReceivableType,
        intended_use: IntendedUse,
        transferrer_user: User,
        decision_reference_number: str,
        decision_maker: DecisionMaker,
        decision_date: datetime.date,
        decision_section: str,
    ):
        now = timezone.now()
        old_service_unit = lease.service_unit

        lease.service_unit = target_service_unit
        lease.lessor = lessor
        lease.intended_use = intended_use
        lease.save(update_fields=["service_unit", "lessor", "intended_use"])

        # Set override_receivable_type on all Rents
        rents: QuerySet[Rent] = lease.rents.all()
        for rent in rents:
            rent.override_receivable_type = receivable_type
            rent.save(update_fields=["override_receivable_type"])

        # Make a copy of Contact's in the new ServiceUnit, keep the old Contact around
        tenants: QuerySet[Tenant] = lease.tenants.all()
        for tenant in tenants:
            original_tenant_contacts = list(
                TenantContact.objects.filter(tenant=tenant).select_related("contact")
            )
            for tenant_contact in original_tenant_contacts:
                contact = tenant_contact.contact
                contact.pk = None
                contact._state.adding = True
                contact.service_unit = (
                    target_service_unit  # Important to update to new service unit
                )
                contact.save()  # Becomes new contact
                tenant_contact.contact = contact  # Switch old contact to new
                tenant_contact.save()  # Save and keep old metadata in the `through` model TenantContact

        # Add note to Collateral's about the ServiceUnit transfer of the Lease
        contracts: QuerySet[Contract] = lease.contracts
        for contract in contracts.all():
            collaterals: QuerySet[Collateral] = contract.collaterals
            transfer_note = self.get_service_unit_transfer_note(
                target_service_unit, old_service_unit, now
            )
            for collateral in collaterals.all():
                if collateral.note:
                    collateral.note = f"{collateral.note} - {transfer_note}"
                else:
                    collateral.note = transfer_note

                collateral.save(update_fields=["note"])

        # Add a Comment about the transfer on the Lease
        comment_topic, _ = CommentTopic.objects.get_or_create(name="Vuokrauksen siirto")
        Comment.objects.create(
            lease=lease,
            topic=comment_topic,
            user=transferrer_user,
            text=self.get_service_unit_transfer_note(
                target_service_unit, old_service_unit, now
            ),
        )

        # Create a Decision for the transfer, with reference being the actual decision made
        decision_type, _ = DecisionType.objects.get_or_create(
            name="Muu päätös",
            kind=DecisionTypeKind.LEASE_SERVICE_UNIT_TRANSFER,
        )
        Decision.objects.create(
            lease=lease,
            reference_number=decision_reference_number,
            decision_maker=decision_maker,
            decision_date=decision_date,
            type=decision_type,
            section=decision_section,
        )

        # Make extra log entry in AuditLog regarding the service unit transfer
        log_entry_manager: LogEntryManager = LogEntry.objects
        log_entry_manager.log_create(
            lease,
            force_log=True,
            action=LogEntry.Action.UPDATE,
            actor=transferrer_user,
            changes={
                "service_unit_transfer": [
                    None,
                    self.get_service_unit_transfer_note(
                        target_service_unit, old_service_unit, now
                    ),
                ]
            },
        )

        logger.info(
            f"Successfully transferred lease {lease.identifier} to {target_service_unit}. "
        )

        return

    def get_service_unit_transfer_note(
        self, target_service_unit, old_service_unit, now: datetime
    ):
        return f"Vuokraus siirretty {now.strftime('%d.%m.%Y')} palveluyksiköstä {old_service_unit} → {target_service_unit}"  # noqa: E501
