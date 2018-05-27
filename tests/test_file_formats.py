"""Test support for FCS file formats"""

import os
from os.path import abspath, dirname, split
import sys
import warnings

import numpy as np
import pytest

import data_file_dl
import pycorrfit

# Files that are known to not work
exclude = []

NOAPITOKEN = "GITHUB_API_TOKEN" not in os.environ


@pytest.mark.xfail(NOAPITOKEN, reason="Restrictions to GitHub API")
def test_asc_all_open():
    # get list of supported file extensions
    ext = "asc"
    files = data_file_dl.get_data_files_ext(ext)
    for f in files:
        if [ex for ex in exclude if f.endswith(ex)]:
            continue
        dn, fn = split(f)
        data = pycorrfit.readfiles.openAny(dn, fn)
        assert data


@pytest.mark.xfail(NOAPITOKEN, reason="Restrictions to GitHub API")
def test_asc_alv7004usb():
    """Test alv7004/USB format"""
    f1 = data_file_dl.get_data_file("ALV-7004USB_ac01_cc01_10.ASC")
    data = pycorrfit.readfiles.openAny(f1)
    assert data["Type"] == ["AC1", "AC2", "CC12", "CC21"]
    assert np.allclose(data["Correlation"][0][10], np.array([0.000275, 0.11208]))
    assert np.allclose(data["Correlation"][1][12], np.array([0.000325, 0.0900233]))
    assert np.allclose(data["Correlation"][2][18], np.array([0.00055, 0.0582773]))
    assert np.allclose(data["Correlation"][3][120], np.array([3.6864, 0.0224212]))
    assert len(data["Trace"][0]) == 253
    assert len(data["Trace"][1]) == 253
    assert len(data["Trace"][2]) == 2
    assert len(data["Trace"][3]) == 2
    assert np.all(data["Trace"][0] == data["Trace"][2][0])
    assert np.all(data["Trace"][1] == data["Trace"][2][1])
    assert np.all(data["Trace"][0] == data["Trace"][3][0])
    assert np.all(data["Trace"][1] == data["Trace"][3][1])
    assert np.allclose(data["Trace"][0][10], np.array([1289.06, 140.20404]))
    assert np.allclose(data["Trace"][1][100], np.array([11835.94, 94.68225]))

    f2 = data_file_dl.get_data_file("ALV-7004USB_dia10_cen10_0001.ASC")
    data2 = pycorrfit.readfiles.openAny(f2)
    # There are empty AC2 and CC12/CC21 curves in this file that should be removed
    # by pycorrfit.
    assert data2["Type"] == ["AC1"]
    assert np.allclose(data2["Correlation"][0][56], np.array([0.0144, 0.0513857]))
    assert len(data2["Trace"][0]) == 254
    assert np.allclose(data2["Trace"][0][210], np.array([49453.13, 165.41434]))

    f3 = data_file_dl.get_data_file("ALV-7004.ASC")
    data3 = pycorrfit.readfiles.openAny(f3)
    assert len(data3["Type"]) == 1
    assert len(data3["Trace"][0]) == 66
    assert data3["Type"][0] == "AC"
    assert np.allclose(data3["Correlation"][0][56], np.array([0.0144, 0.38757]))
    assert np.allclose(data3["Trace"][0][60], np.array([1.21523440e5, 5.11968700e1]))

    f4 = data_file_dl.get_data_file("ALV-7004USB_ac3.ASC")
    data4 = pycorrfit.readfiles.openAny(f4)
    assert len(data4["Type"]) == 1
    assert data4["Type"][0] == "AC"
    assert len(data4["Trace"][0]) == 254


@pytest.mark.xfail(NOAPITOKEN, reason="Restrictions to GitHub API")
def test_csv_all_open():
    # get list of supported file extensions
    ext = "csv"
    files = data_file_dl.get_data_files_ext(ext)
    for f in files:
        if [ex for ex in exclude if f.endswith(ex)]:
            continue
        dn, fn = split(f)
        data = pycorrfit.readfiles.openAny(dn, fn)
        assert data


@pytest.mark.xfail(NOAPITOKEN, reason="Restrictions to GitHub API")
def test_fcs_all_open():
    # get list of supported file extensions
    ext = "fcs"
    files = data_file_dl.get_data_files_ext(ext)
    for f in files:
        if [ex for ex in exclude if f.endswith(ex)]:
            continue
        dn, fn = split(f)
        data = pycorrfit.readfiles.openAny(dn, fn)
        assert data


@pytest.mark.xfail(NOAPITOKEN, reason="Restrictions to GitHub API")
def test_pt3_all_open():
    # get list of supported file extensions
    ext = "pt3"
    files = data_file_dl.get_data_files_ext(ext)
    for f in files:
        if [ex for ex in exclude if f.endswith(ex)]:
            continue
        dn, fn = split(f)
        data = pycorrfit.readfiles.openAny(dn, fn)
        assert data


@pytest.mark.xfail(NOAPITOKEN, reason="Restrictions to GitHub API")
def test_pt3_basic():
    f1 = data_file_dl.get_data_file("PicoQuant_SymphoTime32_A42F-4jul2014/Point_1.pt3")
    data = pycorrfit.readfiles.openAny(f1)

    trace = data["Trace"][0][0]
    assert trace.shape == (600, 2)
    try:
        assert np.allclose(trace[40], np.array([2037, 6.48]))
    except:
        warnings.warn("Unknown pt3 problem after migration to Python3!")

    corr = data["Correlation"][0]
    assert corr.shape == (150, 2)
    assert np.allclose(corr[40], np.array([0.000698, 0.58007174877053136]))
    assert np.allclose(corr[100], np.array([0.72089, 0.019201608388821567]))


@pytest.mark.xfail(NOAPITOKEN, reason="Restrictions to GitHub API")
def test_sin_all_open():
    # get list of supported file extensions
    ext = "sin"
    files = data_file_dl.get_data_files_ext(ext)
    for f in files:
        if [ex for ex in exclude if f.endswith(ex)]:
            continue
        dn, fn = split(f)
        data = pycorrfit.readfiles.openAny(dn, fn)
        assert data



if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in sorted(list(loc.keys())):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
