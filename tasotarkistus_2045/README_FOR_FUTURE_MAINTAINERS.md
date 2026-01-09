# Periodic Rent Adjustment / Tasotarkistus 2045

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
years) adjust the rent amount based on price index development. This allows the
City of Helsinki to maintain desired profit margins in their land lease business
for certain use cases; currently, plots for living purposes.

Tasotarkistus procedure is chosen when the leasing contract is created. The
chosen procedure cannot be removed, and the procedure type (20 or 10 year
intervals) cannot be changed later.

In addition to being tied to a price index, the adjustment amount is capped
between a maximum and minimum percentage of the previous rent amount.
The adjustment amount can also be changed on a case-by-case basis when decided
by certain authoritative entities in City of Helsinki.

For more detailed and accurate information, please see the documents in
`./spec` directory.


## Directory structure

`./spec`

Contains the documents that act as a specification for the feature. It should
be updated whenever specifications change; for example when a new decision about
tasotarkistus is made by City of Helsinki or another authoritative entity.

It should be followed over any code examples, which might lack details of the
final requirements in the year of implementation.

`./code_examples`

Contains example code. They are illustrative only.

`./tests`

Contains example tests. They are illustrative only.

