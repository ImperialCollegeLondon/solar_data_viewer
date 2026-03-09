from model_bakery import baker


def test_SOMagneticField(db):
    """Test SOMagneticField model setup correctly for the external database.

    In particular, that the table name and fields are the expected ones.
    """
    from main.models import SORTNMagneticField

    num = 10
    test_objects = baker.make(SORTNMagneticField, _quantity=num)
    in_db = SORTNMagneticField.objects.all()

    assert len(test_objects) == len(in_db) == num
