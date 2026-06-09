import pandas as pd
import pytest


def make_df(*rows):
    """Build a 3-column DataFrame from (x, y, z) row tuples."""
    return pd.DataFrame(rows, columns=["Bx", "By", "Bz"])


ANGLE_CASES = [
    # label,            (x,  y,  z),          exp_phi,  exp_theta
    ("pos_x_axis", (1, 0, 0), 0.0, 0.0),
    ("pos_y_axis", (0, 1, 0), 90.0, 0.0),
    ("neg_x_axis", (-1, 0, 0), 180.0, 0.0),
    ("neg_y_axis", (0, -1, 0), 270.0, 0.0),
    ("pos_z_axis", (0, 0, 1), 0.0, 90.0),  # phi undefined → 0
    ("neg_z_axis", (0, 0, -1), 0.0, -90.0),  # phi undefined → 0
    ("xy_diagonal", (1, 1, 0), 45.0, 0.0),
    ("xz_diagonal", (1, 0, 1), 0.0, 45.0),
    ("arbitrary", (1, 1, 1), 45.0, 35.2644),
]


def test_known_angles():
    """Computed phi / theta must match hand-calculated reference values."""
    from main.calc import calc_phi_theta

    labels, xyzs, exp_phis, exp_thetas = zip(*ANGLE_CASES)

    input_df = pd.DataFrame(xyzs, columns=["Bx", "By", "Bz"], index=list(labels))
    expected_df = pd.DataFrame(
        {"theta": exp_thetas, "phi": exp_phis},
        index=list(labels),
    )

    result = calc_phi_theta(input_df)

    pd.testing.assert_frame_equal(result, expected_df, atol=1e-3, check_exact=False)


@pytest.mark.parametrize(
    "bad_df",
    [
        pd.DataFrame({"a": [1], "b": [2]}),  # 2 columns
        pd.DataFrame({"a": [1], "b": [2], "c": [3], "d": [4]}),  # 4 columns
        pd.DataFrame({"a": [1]}),  # 1 column
    ],
    ids=["2_cols", "4_cols", "1_col"],
)
def test_wrong_column_count_raises(bad_df):
    """Passing a DataFrame with != 3 columns must raise an AssertionError."""
    from main.calc import calc_phi_theta

    with pytest.raises(AssertionError, match="3 components"):
        calc_phi_theta(bad_df)
