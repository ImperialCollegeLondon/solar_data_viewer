"""Utilities to calculate different parameters."""

import numpy as np
import pandas as pd


def calc_phi_theta(mag: pd.DataFrame) -> pd.DataFrame:
    """Calculate the phi and theta angles out of the B components.

    The dataframe must have 3 components and be ordered X, Y and Z in the relevant
    coordinate system.

    Args:
        mag: DataFrame with 3 columns containing the magnetic field components.

    Returns:
        A dataframe with two columns, phi and theta
    """
    assert len(mag.columns) == 3, (
        "The 3 components of the magnetic field must be provided."
    )

    # Normalize the data
    norm = np.linalg.norm(mag.values, axis=1)
    mag_norm = mag.div(norm, axis="index")

    # Create the output dataframe
    result = pd.DataFrame(index=mag.index)

    # Elevation angle (angle from the xy-plane, range: [-pi/2, pi/2])
    result["theta"] = pd.Series(np.degrees(np.arcsin(mag_norm.iloc[:, 2])))

    # Azimuth angle (angle in the xy-plane, range: [0, 2*pi])
    phi = np.arctan2(mag_norm.iloc[:, 1], mag_norm.iloc[:, 0])
    phi = phi % (2 * np.pi)
    result["phi"] = pd.Series(np.degrees(phi))

    return result


if __name__ == "__main__":
    mag = pd.DataFrame(
        dict(x=[5, 5, 0, 0], y=[0, 5, 0, 5], z=[0, 0, 5, 10]),
        index=["a", "b", "c", "d"],
    )
    phi_theta = calc_phi_theta(mag)
    print(phi_theta)
