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
    phi_gse = models.FloatField(
        help_text="Phi GSE of the magnetic field.", db_column="phi_B_GSE"
    )
    theta_gse = models.FloatField(
        help_text="Theta GSE of the magnetic field.", db_column="theta_B_GSE"
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
        help_text="GSE 'x' component of the magnetic field.", db_column="B_x"
    )
    by_gse = models.FloatField(
        help_text="GSE 'y' component of the magnetic field.", db_column="B_y"
    )
    bz_gse = models.FloatField(
        help_text="GSE 'z' component of the magnetic field.", db_column="B_z"
    )
    b_mag = models.FloatField(
        help_text="Modulus of the magnetic field.", db_column="B_mod"
    )
    phi_gse = models.FloatField(
        help_text="Phi GSE of the magnetic field.", db_column="phi_B_GSE"
    )
    theta_gse = models.FloatField(
        help_text="Theta GSE of the magnetic field.", db_column="theta_B_GSE"
    )

    class Meta:  # noqa: D106
        db_table = "solo_L2_mag-gse-ll-internal"
        managed = False


class SOContactSchedule(models.Model):
    """Model describing spacecraft SO contact schedule, also known as passes."""

    start_time = models.DateTimeField(help_text="Start time of the pass")
    end_time = models.DateTimeField(help_text="End time of the pass")

    class Meta:  # noqa: D106
        db_table = "contact_schedule"
        managed = False


class IMAPSWAPI(models.Model):
    """Model describing the SWAPI data for IMAP."""

    time = models.DateTimeField(
        primary_key=True,
        null=False,
        help_text="Time for the data.",
        db_column="id",
    )

    density = models.FloatField(
        help_text="Proton density in cm^-3.", db_column="swapi_pseudo_proton_density"
    )
    speed = models.FloatField(
        help_text="Proton speed in km/s.", db_column="swapi_pseudo_proton_speed"
    )
    temperature = models.FloatField(
        help_text="Proton temperature in K.",
        db_column="swapi_pseudo_proton_temperature",
    )

    class Meta:  # noqa: D106
        db_table = "ialirt_swapi"
        managed = False


MAG_MODELS = {"IMAP": IMAPGSEMagneticField, "SO": SOGSEMagneticField}
"""Models to handle magnetic data for the supported missions."""
