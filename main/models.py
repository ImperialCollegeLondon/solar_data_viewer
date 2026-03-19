"""Models for the main app."""

from django.db import models


class IMAPGSEMagneticField(models.Model):
    """Model describing the GSE components of the magnetic field."""

    time = models.DateTimeField(
        primary_key=True,
        null=False,
        help_text="Time for the data.",
        db_column="time_utc",
    )

    bx_gse = models.FloatField(
        help_text="GSE 'x' component of the magnetic field.", db_column="B_GSE_x"
    )
    by_gse = models.FloatField(
        help_text="GSE 'y' component of the magnetic field.", db_column="B_GSE_y"
    )
    bz_gse = models.FloatField(
        help_text="GSE 'z' component of the magnetic field.", db_column="B_GSE_z"
    )
    b_mag = models.FloatField(
        help_text="Modulus of the magnetic field.", db_column="B_magnitude"
    )

    class Meta:  # noqa: D106
        db_table = "ialirt_mag"
        managed = False


class SOGSEMagneticField(models.Model):
    """Model describing the GSE components of the magnetic field."""

    time = models.DateTimeField(
        primary_key=True,
        null=False,
        help_text="Time for the data.",
        db_column="time",
    )

    bx_gse = models.FloatField(
        help_text="GSE 'x' component of the magnetic field.", db_column="B_GSE_x"
    )
    by_gse = models.FloatField(
        help_text="GSE 'y' component of the magnetic field.", db_column="B_GSE_y"
    )
    bz_gse = models.FloatField(
        help_text="GSE 'z' component of the magnetic field.", db_column="B_GSE_z"
    )
    b_mag = models.FloatField(
        help_text="Modulus of the magnetic field.", db_column="B_mod"
    )

    class Meta:  # noqa: D106
        db_table = "solo_L2_mag-gse-ll-internal"
        managed = False


class TrajectoryCache(models.Model):
    """Model to hold the cached trajectory data."""

    _PLOTS = (("SO", "SO"), ("L1", "L1"))

    plot = models.CharField(
        choices=_PLOTS,
        unique=True,
        null=False,
        blank=False,
        help_text="The plot the trajectory data is for.",
    )
    data = models.JSONField(
        null=False, blank=False, default=dict, help_text="The trajectory data to store."
    )
    time_generated = models.CharField(
        null=False,
        blank=False,
        help_text="The time the data was generated in string format.",
    )


MAG_MODELS = {"IMAP": IMAPGSEMagneticField, "SO": SOGSEMagneticField}
"""Models to handle magnetic data for the supported missions."""
