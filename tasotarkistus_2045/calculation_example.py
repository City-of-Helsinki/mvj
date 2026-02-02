"""
This file contains an example calculation for tasotarkistus in 2045.

It is based on an Excel file used by the City of Helsinki to draft the
tasotarkistus calculation specification. It might differ from the final
specification.

It is for illustration purposes only and is not used in the actual application.

Please refer to [specification.md](./specification.md)
"""

from decimal import Decimal


def calculate_yearly_rent(
    base_rent: Decimal, previous_index: Decimal, base_index: Decimal
) -> Decimal:
    """
    base_rent: Base rent value (PV_0, "PerusVuokra")
    previous_index: Previous year's average value of consumer price index
                    (E_n-1, "Elinkustannusindeksi")
    base_index: Base value for consumer price index (E_0, "Elinkustannusindeksi")
    """
    return (base_rent * (previous_index / base_index)).quantize(Decimal("0.01"))


def calculate_tasotarkistus_rent(
    base_rent: Decimal, average_index: Decimal, base_index: Decimal
) -> Decimal:
    """
    base_rent: Base rent value (PV_0, "PerusVuokra")
    average_index: Average value of housing company price index over
                   the previous 3 years (A_avg, "Asunto-osakeyhtiöiden
                   hintakehitysindeksi")
    base_index: Base value for price index of old dwellings in housing companies
                (A_0, "Asunto-osakeyhtiöiden hintakehitysindeksi")
    """
    return (base_rent * (average_index / base_index)).quantize(Decimal("0.01"))


def calculate_percentage_tasotarkistus_vs_yearly_rent(
    tasotarkistus_rent: Decimal, yearly_rent: Decimal
) -> Decimal:
    """
    Calculates the percentage of tasotarkistus rent against yearly rent,
    to determine the adjustment limits.

    tasotarkistus_rent: Rent calculated with tasotarkistus (T_n)
    yearly_rent: Yearly rent before tasotarkistus (V_n-1, "vuotuinen Vuokra")
    """
    return (tasotarkistus_rent / yearly_rent * Decimal(100)).quantize(Decimal("0.01"))


# Rent start year 2025
# Base year for the index values: 2024

# Base value for consumer price index (1951=100), "Elinkustannusindeksi"
# The previous year's average value.
E_0 = Decimal(2332)

# Base value for price index of old dwellings in housing companies.
# "Asunto-osakeyhtiöiden hintakehitysindeksi"
# The previous year's average value.
A_0 = Decimal("93.2")

# Base rent value, "PerusVuokra"
PV_0 = Decimal(123000)

# Yearly adjusted rent before the first tasotarkistus interval.
# "vuotuinen Vuokra"
# Example for year 2035:
E_9 = Decimal(2500)  # guess for year 2034
V_10 = calculate_yearly_rent(base_rent=PV_0, previous_index=E_9, base_index=E_0)
assert V_10 == Decimal("131861.06")


# ============ First tasotarkistus interval ===========

# This happens 20 years after rent start year.

# Yearly rent 1 year before first tasotarkistus
E_18 = Decimal(2950)  # guess for year 2043
V_19 = calculate_yearly_rent(base_rent=PV_0, previous_index=E_18, base_index=E_0)
assert V_19 == Decimal("155596.05")

# Housing company price index value 1 year before first tasotarkistus is
# calculated as the average of the previous 3 years' index values.
# "Asunto-osakeyhtiöiden hintakehitysindeksi"
A_17 = Decimal(240)  # guess for year 2042
A_18 = Decimal(250)  # guess for year 2043
A_19 = Decimal(260)  # guess for year 2044
A_avg1 = ((A_17 + A_18 + A_19) / Decimal(3)).quantize(Decimal("0.01"))
assert A_avg1 == Decimal("250.00")

# Rent calculated with ratio of the housing price index
T_20 = calculate_tasotarkistus_rent(
    base_rent=PV_0, average_index=A_avg1, base_index=A_0
)
assert T_20 == Decimal("329935.62")

# Percentage of tasotarkistus value against regular yearly rent calculation
# "Tasotarkistus vs Vuokra Prosentti"
TVP_20 = calculate_percentage_tasotarkistus_vs_yearly_rent(
    tasotarkistus_rent=T_20, yearly_rent=V_19
)
assert TVP_20 == Decimal("212.05")

# The new yearly rent with tasotarkistus applied.
# In the first tasotarkistus interval, the change is capped to maximum of 50%
# increase or decrease from previous yearly rent.
if TVP_20 > Decimal(150):
    PV_20 = (V_19 * Decimal(1.5)).quantize(Decimal("0.01"))
elif TVP_20 < Decimal(50):
    PV_20 = (V_19 * Decimal(0.5)).quantize(Decimal("0.01"))
else:
    PV_20 = T_20

# In this case the tasotarkistus rent exceeds the 50% increase limit, so the
# new rent is capped to 50% increase from previous year's rent.
assert PV_20 == (V_19 * Decimal("1.5")).quantize(Decimal("0.01"))
assert PV_20 == Decimal("233394.08")

# NOTE: A custom consideration ("harkinta") can be applied here to adjust the
# yearly rent further, on a decision from an authoritative body in Helsinki.
# For now, don't apply any consideration.

# Consumer price index value 1 year before first tasotarkistus
# This will be the new base index (previously E_0) for yearly rent calculation
# after this tasotarkistus.
E_19 = Decimal(3000)  # guess for year 2044

# Yearly adjusted rent between first and second tasotarkistus.
# Example  for year 2050
E_24 = Decimal(3200)  # guess for year 2049
V_25 = calculate_yearly_rent(base_rent=PV_20, previous_index=E_24, base_index=E_19)
assert V_25 == Decimal("248953.69")


# ============ Second tasotarkistus interval ===========

# This happens 20 or 10 years after the first tasotarkistus, depending on the
# chosen interval length.
# NOTE: Maximum increase/decrease limits for the second tasotarkistus interval
# are lower for interval length of 10: 25% increase/decrease instead of 50%.

# Yearly rent 1 year before second tasotarkistus
E_38 = Decimal(4400)  # guess for year 2063
V_39 = calculate_yearly_rent(base_rent=PV_20, previous_index=E_38, base_index=E_19)
assert V_39.quantize(Decimal("0.01")) == Decimal("342311.32")

# Housing company price index value 1 year before second tasotarkistus is
# calculated as the average of the previous 3 years' index values.
A_37 = Decimal(440)  # guess for year 2062
A_38 = Decimal(450)  # guess for year 2063
A_39 = Decimal(460)  # guess for year 2064
A_avg2 = ((A_37 + A_38 + A_39) / Decimal(3)).quantize(Decimal("0.01"))
assert A_avg2.quantize(Decimal("0.01")) == Decimal("450.00")

# Rent calculated with ratio of the housing price index
T_40 = calculate_tasotarkistus_rent(
    base_rent=PV_0, average_index=A_avg2, base_index=A_avg1
)
assert T_40 == Decimal("221400.00")

# Percentage of tasotarkistus value against regular yearly rent calculation
TVP_40 = calculate_percentage_tasotarkistus_vs_yearly_rent(
    tasotarkistus_rent=T_40, yearly_rent=V_39
)
assert TVP_40 == Decimal("64.68")

# The new yearly rent with tasotarkistus applied.
# In the second tasotarkistus interval, the change is capped to maximum of:
#   * 50% increase or decrease from previous yearly rent for 20 year interval
#   * 25% increase or decrease from previous yearly rent for 10 year interval
# This calculation assumes 20 year interval.
if TVP_40 > Decimal(150):
    PV_40 = (V_39 * Decimal(1.5)).quantize(Decimal("0.01"))
elif TVP_40 < Decimal(50):
    PV_40 = (V_39 * Decimal(0.5)).quantize(Decimal("0.01"))
else:
    PV_40 = T_40

# This time the tasotarkistus rent is lower than previous year's rent, but
# within the limits, so it's applied as is.
assert PV_40 == T_40
assert PV_40 == Decimal("221400.00")

# NOTE: A custom consideration ("harkinta") can be applied here to adjust the
# yearly rent further, on a decision from an authoritative body in Helsinki.
# For now, don't apply any consideration.

# Consumer price index value 1 year before second tasotarkistus
# This will be the new base index (previously E_19) for yearly rent calculation
# after this tasotarkistus interval.
E_39 = Decimal(4500)  # guess for year 2064

# Yearly adjusted rent between the second and third tasotarkistus.
# Example for year 2050:
E_44 = Decimal(5000)  # guess for year 2049
V_45 = calculate_yearly_rent(base_rent=PV_40, previous_index=E_44, base_index=E_39)
assert V_45 == Decimal("246000.00")

# =========== Subsequent tasotarkistus intervals ===========

# The calculation logic for subsequent tasotarkistus intervals is the same
# as for the second interval.
# The only difference is the base index values and base rent values used for the
# calculations, which are updated at each tasotarkistus.

# NOTE: You need to save the adjustment details that represent the newly
# adjusted rent, with history of the changes:
#   * Dates of tasotarkistus adjustments at 20, (30), 40, (50), 60, ... years
#     after rent start.
#   * New rent base amounts PV_n after each adjustment (PV_20, PV_40,
#     PV_60, ...  )
#   * New base value E_(n-1) for the consumer price index calculations
#     between tasotarkistus intervals (E_19, E_39, E_59, ...)
#   * Average housing company price index values A_avg_n used in each
#     tasotarkistus (A_avg1, A_avg2, A_avg3, ...)
#   * Anything else that might be necessary for future calculations.
#
# This will be necessary to properly calculate and audit the invoices,
# especially if the adjustment happens mid-invoicing-period.
