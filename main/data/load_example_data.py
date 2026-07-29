"""This script populates the DB with fresh data, removing the old one, if any.

If run with docker compose, new data will be in the db for the right time range,
as if it were being received sort of 'live' whenever the tool is launched.
"""

import numpy as np
import pandas as pd
from django.utils import timezone

from main.models import IMAPSWAPI, MAG_MODELS, SOContactSchedule

# Define the times
now = timezone.now()

########################################################################################
# Load magnetic field data for both IMAP and SO
########################################################################################

mfield_times = pd.date_range(
    start=now - pd.Timedelta(days=10), end=now, freq="20s"
).to_series()

# For each of the supported spacecrafts we add some data
for model in MAG_MODELS.values():
    # First we get rid of all the objects in the DB
    model.objects.all().delete()  # type: ignore[attr-defined]

    # Now, we create new magnetic fields
    b = np.random.rand(len(mfield_times), 5)
    b[:, 0] += 1
    b[:, 1] -= 1
    mfield = [
        model(
            time=t,
            bx_gse=row[0],
            by_gse=row[1],
            bz_gse=row[2],
            b_mag=np.linalg.norm(row[:3]),
            phi_gse=row[3],
            theta_gse=row[4],
        )
        for t, row in zip(mfield_times, b)
    ]

    # And add it to the DB in bulk
    model.objects.bulk_create(mfield)  # type: ignore[attr-defined]

########################################################################################
# Load IMAP SWAPI data
########################################################################################

swapi_times = pd.date_range(
    start=now - pd.Timedelta(days=10), end=now, freq="20s"
).to_series()

# Remove existing SWAPI rows and replace with fresh examples.
IMAPSWAPI.objects.all().delete()

# Add data
density = np.random.normal(loc=3.95, scale=0.22, size=len(swapi_times))
speed = np.random.normal(loc=388.5, scale=0.6, size=len(swapi_times))
temperature = np.random.normal(loc=27400, scale=380, size=len(swapi_times))

density = density.clip(3.55, 4.35).round(2)
speed = speed.clip(387, 390).round(2)
temperature = temperature.clip(26600, 28200).round(2)

swapi_data = [
    IMAPSWAPI(
        time=t,
        density=density_i,
        speed=speed_i,
        temperature=temperature_i,
    )
    for t, density_i, speed_i, temperature_i in zip(
        swapi_times, density, speed, temperature
    )
]

# Add the data to the DB in bulk
IMAPSWAPI.objects.bulk_create(swapi_data)

########################################################################################
# Load SO contact schedule (pass) data
########################################################################################

# Generate passes for the next 30 days, one every 2 days
pass_times = pd.date_range(
    start=now + pd.Timedelta(days=0), end=now + pd.Timedelta(days=30), freq="2D"
).to_series()

# Delete existing passes for SO
SOContactSchedule.objects.all().delete()

# Create SOContactSchedule objects
passes = []
for start in pass_times:
    end = start + pd.Timedelta(hours=1)  # 1 hour pass
    passes.append(
        SOContactSchedule(
            start_time=start,
            end_time=end,
        )
    )

# Add the new passes to the DB in bulk
SOContactSchedule.objects.bulk_create(passes)
