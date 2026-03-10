"""This script populates the DB with fresh data, removing the old one, if any.

If run with docker compose, new data will be in the db for the right time range,
as if it were being received sort of 'live' whenever the tool is launched.
"""

import numpy as np
import pandas as pd
from django.utils import timezone

from main.models import IMAPGSEMagneticField

# First we get rid of all the objects in the DB
IMAPGSEMagneticField.objects.all().delete()

# Now, we create new content
now = timezone.now()
times = pd.date_range(
    start=now - pd.Timedelta(days=10), end=now, freq="min"
).to_series()
b = np.random.rand(len(times), 4)
mfield = [
    IMAPGSEMagneticField(
        time=times.iloc[i],
        bx_gse=b[i, 0],
        by_gse=b[i, 1],
        bz_gse=b[i, 2],
        b_mag=b[i, 3],
    )
    for i in range(len(times))
]

# And add it to the DB in bulk
IMAPGSEMagneticField.objects.bulk_create(mfield)
