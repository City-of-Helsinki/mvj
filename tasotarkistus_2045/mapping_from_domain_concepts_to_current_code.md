# Mapping from domain concepts to current code

## Purpose

This document describes how the existing codebase currently represents
and processes the domain concepts related to Tasotarkistus / Periodic Rent
Adjustment.

Future systems should treat these code references as historical context only.
The authoritative description of behavior is in [specification.md](./specification.md)

### Concept: Periodic rent adjustment (Tasotarkistus)

#### Current Code

See all following concepts in this file for more detailed code references.

#### Meaning

In a nutshell, tasotarkistus is a procedure to periodically (e.g. every 20 or 10
years) adjust the rent amount based on price index development.

For more details, see the documentation in [specification.md](./specification.md)

#### Notes on current code

The codebase does not have a single entity containing or describing the
functionality related to tasotarkistus.
See all the following concepts in this file for more details.

---

### Concept: Periodic rent adjustment type

#### Current code

* leasing.enums.PeriodicRentAdjustmentType
* leasing.models.rent.Rent.periodic_rent_adjustment_type

#### Meaning

In Finnish: "Tasotarkistuksen tyyppi"

Type of the periodic rent adjustment dictates how often the adjustment is
applied. These are the only two options available currently:
- first at 20 years, then every 20 years afterwards, or
- first at 20 years, then every 10 years afterwards.

The type is decided at the time of writing the leasing contract.
Type cannot be changed after signing the contract.

#### Notes on current code

Type of the periodic rent adjustment is saved to each relevant rent's property
`leasing.models.rent.Rent.periodic_rent_adjustment_type`.

---

### Concept: Price index

#### Current code

* leasing.management.commands.import_periodic_rent_adjustment_price_index
* leasing.models.rent.OldDwellingsInHousingCompaniesPriceIndex
* leasing.models.rent.Rent.old_dwellings_in_housing_companies_price_index

#### Meaning

The price index and its point figure values are the primary indicator for rent
amount adjustments in tasotarkistus.

`Old dwellings in housing companies price index` translates to "Vanhojen
osakeasuntojen hintaindeksi" in Finnish. The series 2020=100 was the desired
starting point during specification.

#### Notes on current code

Index data is provided by StatFin (in Finnish: Tilastokeskus).

Index data is fetched with a Django management command. See
`leasing.management.commands.import_periodic_rent_adjustment_index`.

If Helsinki decides to use a different price index, you need to update the
importing functionality with the desired API request details.
The correct data set is uniquely identified by:
- API URL, which contains a set of indexes at a given resolution (e.g. quarterly, or yearly)
- code that identifies the index (e.g. `ketj_P_QA_T`, which corresponds to "vanhojen osakeasuntojen hintaindeksi")
- geographical region (e.g. `pks`, or "pääkaupunkiseutu" in Finnish)

Index details are saved to database. See table
`leasing_olddwellingsinhousingcompaniespriceindex`.

If a reference to the price index is set to a rent instance, that rent uses the
tasotarkistus procedure. This means the rent amount needs to be re-calculated in
2045. See
`leasing.models.rent.Rent.old_dwellings_in_housing_companies_price_index`.

---

### Concept: Index point figure

#### Current code

* leasing.management.commands.import_periodic_rent_adjustment_index
* leasing.management.commands.update_missing_periodic_rent_adjustment_index_values
* leasing.models.rent.IndexPointFigureYearly
* leasing.models.rent.Rent.start_price_index_point_figure_value
* leasing.models.rent.Rent.start_price_index_point_figure_year

#### Meaning

The price index and its point figure values are the primary indicator for rent
amount adjustments in tasotarkistus. Index data is provided by StatFin (in
Finnish: Tilastokeskus).

`Index point figure, yearly` translates to "Indeksipisteluku, vuosittainen" in
Finnish. In this case, their numerical values between different years indicate
the relative increase or decrease of a plot's rent.

#### Notes on current code

Index data is provided by StatFin (in Finnish: Tilastokeskus).

Point figure data is fetched with a Django management command. See
`leasing.management.commands.import_periodic_rent_adjustment_index`.
Each figure is uniquely identified by the combination of:
- index's database ID (e.g. `1`)
- region (e.g. `pks`, which is short for "pääkaupunkiseutu" in Finnish)
- year (e.g. `2025`)

Point figures are saved to database. See table `leasing_indexpointfigureyearly`.

The value and year of the price index's current point figure are added to each
Rent object when the rent is created, if it uses tasotarkistus.
This is intended to add a layer of redundancy, in case the point figure table
would be lost. See
- `leasing.models.rent.Rent.start_price_index_point_figure_value`
- `leasing.models.rent.Rent.start_price_index_point_figure_year`

If the previous year's point figure is not available from StatFin at the time of
creating the rent, the starting value and year are left blank, and added
retroactively when they become available. See
- `leasing.management.commands.update_missing_periodic_rent_adjustment_index_values`


---
