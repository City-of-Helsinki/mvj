"""
Updates intended uses in leases based on a JSON file.

At this time this is only intended for MAKE intended uses (service unit ID = 1).

Expected JSON file input format:
[
  {
    "id": 1,                      # primary key in the temporary table
    "create_time": <timestamp>,   # or null. Not used in this script.
    "old_name": "name 1"          # name of the OLD intended use
    "new_name": "name 2"          # name of the NEW intended use. Not used in this script.
    "old_id": 1,                  # primary key of the OLD intended use
    "new_id": 2,                  # primary key of the NEW intended use
  },
  {
  ...
  }
]

Iterates through all leases, and for each lease, iterates through the JSON items,
and if lease.intended_use_id == old_id:

1. lease.intended_use_id = new_id
2. lease.intended_use_note = lease.intended_use_note + " Vanha: <old_name>"
"""

import argparse
import json
import logging
import os
import sys
from typing import TypedDict

import django

# Set up the Django environment without being a management command
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mvj.settings")
django.setup()

from leasing.models import IntendedUse, Lease  # noqa: E402

DEFAULT_INPUT_FILENAME = "tmp_intended_use.json"
TARGET_SERVICE_UNIT_ID = (
    1  # Ensures only the intended uses from the correct service unit are updated
)

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)


class IntendedUseUpdateDetails(TypedDict):
    id: int
    create_time: str | None
    old_name: str
    new_name: str
    old_id: int
    new_id: int


def parse_args():
    parser = argparse.ArgumentParser(
        description="Updates intended uses in leases based on a JSON file."
    )
    parser.add_argument(
        "input_file",
        help="Path to the JSON file containing intended use updates",
        nargs="?",
        default=DEFAULT_INPUT_FILENAME,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would be done without making changes",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_file = args.input_file
    dry_run: bool = args.dry_run

    with open(input_file, "r", encoding="utf-8") as f:
        intended_use_update_details = json.load(f)
        logger.info(
            f"Read {len(intended_use_update_details)} intended use updates from {input_file}"
        )

    update_lease_intended_uses(
        intended_use_update_details, TARGET_SERVICE_UNIT_ID, dry_run
    )


def update_lease_intended_uses(
    intended_use_update_details: list[IntendedUseUpdateDetails],
    target_service_unit_id: int,
    dry_run: bool = True,
):
    assert no_duplicate_old_ids(intended_use_update_details)
    assert intended_uses_are_from_correct_service_unit(
        intended_use_update_details, target_service_unit_id
    )
    assert new_ids_exist_in_db(intended_use_update_details)

    old_id_to_details = {
        update_details["old_id"]: update_details
        for update_details in intended_use_update_details
    }

    lease_counter = 0
    updated_leases = 0
    all_leases = Lease.objects.all()
    logger.info(f"Found {len(all_leases)} leases in the database.")
    logger.info("Processing...")

    for lease in all_leases:
        if lease_counter % 1000 == 0 and lease_counter > 0:
            logger.info(f"Progress: {lease_counter} leases processed.")

        lease_counter += 1
        updated = update_lease_intended_use_if_needed(
            lease, old_id_to_details, target_service_unit_id, dry_run
        )

        if updated:
            updated_leases += 1

    logger.info(f"Updated {updated_leases} leases in total.")


def update_lease_intended_use_if_needed(
    lease: Lease,
    old_id_to_details: dict[int, IntendedUseUpdateDetails],
    target_service_unit_id: int,
    dry_run: bool,
) -> bool:
    """
    Update a lease's intended use if changes are needed.

    Returns True if the lease was updated, False otherwise.
    """
    if lease.service_unit.pk != target_service_unit_id:
        # This lease is not from the target service unit --> safe to skip
        return False

    old_intended_use = lease.intended_use

    if not old_intended_use or old_intended_use.pk not in old_id_to_details:
        # This lease's intended use is not mentioned in the input file--> safe to skip
        return False

    update_details = old_id_to_details[old_intended_use.pk]
    old_id = update_details["old_id"]
    new_id = update_details["new_id"]
    old_name = update_details["old_name"]

    new_intended_use = IntendedUse.objects.get(pk=new_id)

    if new_intended_use.service_unit.pk != target_service_unit_id:
        # The new intended use is from wrong service unit.
        # This should not happen because we check the service units in function
        # intended_uses_are_from_correct_service_unit() before this function is called.
        raise ValueError(
            f"New intended use {new_id} is from wrong service unit {new_intended_use.service_unit.pk}. "
            "Fix the input file to avoid problems."
        )

    id_changed = old_id != new_intended_use.pk
    name_changed = old_name != new_intended_use.name

    if id_changed:
        update_lease_intended_use(lease, new_intended_use, old_id, dry_run)

    if name_changed:
        note_changed = update_lease_intended_use_note_if_changed(
            lease, old_name, dry_run
        )
    else:
        note_changed = False

    if id_changed or note_changed:
        if dry_run:
            logger.info(f"Would save lease {lease.pk}")
            return False
        else:
            lease.save()
            return True

    return False


def no_duplicate_old_ids(
    intended_use_update_details: list[IntendedUseUpdateDetails],
) -> bool:
    old_ids = {}
    for update_details in intended_use_update_details:
        old_id = update_details["old_id"]
        if old_id in old_ids:
            logger.error(
                f"Duplicate old_id {old_id} found. Fix this in the input file to avoid problems."
            )
            return False

    return True


def intended_uses_are_from_correct_service_unit(
    intended_use_update_details: list[IntendedUseUpdateDetails],
    target_service_unit_id: int,
) -> bool:
    """
    Verify that all intended uses in the input file are from the correct service unit.
    """
    old_ids = {details["old_id"] for details in intended_use_update_details}
    new_ids = {details["new_id"] for details in intended_use_update_details}
    all_ids = old_ids | new_ids

    intended_uses = IntendedUse.objects.filter(pk__in=all_ids)
    intended_uses_from_other_service_units = intended_uses.exclude(
        service_unit_id=target_service_unit_id
    )
    if intended_uses_from_other_service_units.exists():
        other_service_unit_ids = intended_uses_from_other_service_units.values_list(
            "service_unit_id", flat=True
        )
        logger.error(
            f"Intended uses {intended_uses_from_other_service_units} are from wrong service unit(s) "
            f"{other_service_unit_ids}. Fix the input file to avoid problems."
        )
        return False

    return True


def new_ids_exist_in_db(
    intended_use_update_details: list[IntendedUseUpdateDetails],
) -> bool:
    """Verify that all incoming ID's are in the database, to avoid problems during the update."""
    new_ids = {details["new_id"] for details in intended_use_update_details}
    existing_ids = set(IntendedUse.objects.values_list("pk", flat=True))
    missing_ids = new_ids - existing_ids

    if missing_ids:
        logger.error(
            f"New intended use IDs {missing_ids} not found in the database. "
            "Add them to the database before running this script."
        )
        return False

    return True


def update_lease_intended_use(
    lease: Lease,
    new_intended_use: IntendedUse,
    old_id: int,
    dry_run: bool,
) -> None:
    if dry_run:
        logger.info(f"Would update intended use from {old_id} to {new_intended_use.pk}")
    else:
        lease.intended_use = new_intended_use


def update_lease_intended_use_note_if_changed(
    lease: Lease,
    old_name: str,
    dry_run: bool,
) -> bool:
    """
    Updates lease.intended_use_note if it is not already set to the new value.

    Returns True if the note was updated and lease needs to be saved, False otherwise.
    """
    note = lease.intended_use_note or ""
    note_addition = f"Vanha: {old_name}"
    note_changed = not note.endswith(note_addition)

    if note_changed:
        if dry_run:
            logger.info(f"Would add note: Vanha: {old_name}")
        else:
            updated_note = f"{note} {note_addition}" if note else note_addition
            lease.intended_use_note = updated_note

        return True

    return False


if __name__ == "__main__":
    logger.info("Starting the script")
    main()
    logger.info("Done.")
