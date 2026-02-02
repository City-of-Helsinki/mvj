# Tasotarkistus 2045 / Periodic Rent Adjustment

For original source material, please see [specification.md](./specification.md)

## Who is this directory for

This directory contains the current understanding of the feature "Periodic rent
adjustment", or "Tasotarkistus" in Finnish, to serve the future maintainers of
MVJ/Maanvuokrausjärjestelmä.

The feature will become relevant by year 2045 at the latest, when the first
adjustments come into effect.
Nothing can be assumed about the future "MVJ" system of that time, which is why
the feature is not finalized at this time of writing.


## What is tasotarkistus / periodic rent adjustment

In a nutshell, tasotarkistus is a procedure to periodically (e.g. every 20 or 10
years) adjust the rent amount based on price index development. The goal is for
long-time leases to follow the land's market value changes in a fair and
impartial way, especially regarding plots for living purposes.

Tasotarkistus procedure is chosen when the leasing contract is created. The
chosen procedure cannot be removed, and the procedure type (20 or 10 year
intervals) cannot be changed later.

In addition to being tied to a price index, the adjustment amount is capped
between a maximum and minimum percentage of the previous rent amount.

The adjustment amount can also be changed on a case-by-case basis when decided
by certain authoritative entities in City of Helsinki.

Relying on manual invoice fixes after the adjustment must be avoided.
E.g. if the adjustment is performed mid-invoicing-period for a rent, make sure
to add logic to properly update the data to consider such out-of-cycle change.

You might need to keep a record of all tasotarkistus details across the years
for the affected rent, to ensure accurate invoicing, auditability and
reversibility:
- original value before this adjustment
- date of this adjustment
- new value after this adjustment
- other details that affected this calculation result
- ... repeat for all adjustments across the years

For original source material, please see [specification.md](./specification.md)


## Official specification

The `./spec` directory contains the documents that act as a specification for
the feature. It should be updated whenever specifications change; for example
when a new decision about tasotarkistus is made by City of Helsinki or another
authoritative entity.

It should be followed over any code examples, which might lack details of the
final requirements in the year of implementation.

You might need to use alternative sources to find the most recent authoritative
specification of the feature, if the ones included here are not the latest ones.
