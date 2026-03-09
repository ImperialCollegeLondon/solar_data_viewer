"""Models for the main app."""

from django.db import models


class BaseRTNMagneticField(models.Model):
    """Model describing the components of the magnetic field on a specific datetime."""

    time = models.DateTimeField(
        primary_key=True, null=False, help_text="Time for the data."
    )
    B_r = models.FloatField(help_text="'r' component of the magnetic field.")
    B_t = models.FloatField(help_text="'t' component of the magnetic field.")
    B_n = models.FloatField(help_text="'n' component of the magnetic field.")
    B_mod = models.FloatField(help_text="Modulus of the magnetic field.")

    class Meta:  # noqa: D106
        abstract = True


class SORTNMagneticField(BaseRTNMagneticField):
    """Magnetic field model for the Solar Orbiter mission."""

    class Meta:  # noqa: D106
        db_table = "solo_L2_mag-rtn-ll-internal"
        managed = False
