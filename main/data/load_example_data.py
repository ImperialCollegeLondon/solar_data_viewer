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
    b = np.random.rand(len(times), 3)
    mfield = [
        model(
            time=times.iloc[i],
            bx_gse=b[i, 0] + 1,
            by_gse=b[i, 1] - 1,
            bz_gse=b[i, 2],
            b_mag=(b[i, 0] + 1) ** 2 + (b[i, 1] - 1) ** 2 + (b[i, 2]) ** 2,
        )
        for i in range(len(times))
    ]

    # And add it to the DB in bulk
    model.objects.bulk_create(mfield)  # type: ignore[attr-defined]
