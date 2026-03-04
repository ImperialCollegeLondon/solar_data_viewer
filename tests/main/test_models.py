import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_SOMagneticField():
    """Test SOMagneticField model setup correctly for the external database.

    In particular, that the table name and fields are the expected ones.
    """
    from main.models import SOMagneticField

    num = 10
    test_objects = baker.make(SOMagneticField, _quantity=num)
    in_db = SOMagneticField.objects.all()

    assert len(test_objects) == len(in_db) == num
