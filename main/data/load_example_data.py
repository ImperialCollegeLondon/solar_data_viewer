"""This script populates the DB with fresh data, removing the old one, if any.

If run with docker compose, new data will be in the db for the right time range,
as if it were being received sort of 'live' whenever the tool is launched.
"""

import numpy as np
import pandas as pd
from django.utils import timezone

from main.models import MAG_MODELS

# Define the times
now = timezone.now()
times = pd.date_range(
    start=now - pd.Timedelta(days=10), end=now, freq="min"
).to_series()

# For each of the supported spacecrafts we add some data
for model in MAG_MODELS.values():
    # First we get rid of all the objects in the DB
    model.objects.all().delete()  # type: ignore[attr-defined]

    # Now, we create new magnetic fields
    b = np.random.rand(len(times), 4)
    b[:, 0] += 1
    b[:, 1] -= 1
    mfield = [
        model(
            time=t,
            bx_gse=row[0],
            by_gse=row[1],
            bz_gse=row[2],
            b_mag=np.linalg.norm(row),
            phi_gse=row[3],
        )
        for t, row in zip(times, b)
    ]

    # And add it to the DB in bulk
    model.objects.bulk_create(mfield)  # type: ignore[attr-defined]
