import pandas
import pytest
import synnax as sy
from mcnugget.cli.instrument import (
    Context,
    create_device_channels,
    process_source,
    process_valve,
    process_tc,
    process_pt
)

"""
These are unit tests for instrument.py
They test all aspects of the code except reading for the conversion from a filepath/google sheet to a pandas.DataFrame
"""

client = sy.Synnax(
    host="localhost",
    port=9090,
    username="synnax",
    password="seldon",
    secure=False,
)
rng = client.ranges.create(
    name="Test Active Range",
    time_range=sy.TimeRange(
        start=sy.TimeStamp.now(),
        end=sy.TimeStamp.now() + 5 * sy.TimeSpan.SECOND,
    ),
)
client.ranges.set_active(rng.key)
ctx = Context(client=client, active_range=rng, indexes=dict())
test_df = {
   'Name': ['vlv_test_1', 'vlv_test_2', 'lox_mpv', 'testing valve', 'vlv_test_3', 'vlv_test_4', 'valve_23', 'pt_test_1',
            'pt_test_2', 'pt_test_3', 'pt_test_4', 'pt_test_5', 'pt_test_6', 'tc_test_1', 'tc_test_2', 'tc_test_3'],
   'Device': ['gse', 'gse', 'gse', 'gse', 'gse', 'gse', 'gse', 'gse', 'gse', 'gse', 'gse', 'gse', 'gse', 'gse', 'gse', 'gse'],
   'Port': [0, 1, 2, 19, 20, 21, 22, 0, 1, 2, 3, 4, 5, 0, 1, 2],
   'Type': ['VLV', 'VLV', 'VLV', 'VLV', 'VLV', 'VLV', 'VLV', 'PT', 'PT', 'PT', 'PT', 'PT', 'PT', 'TC', 'TC', 'TC'],
   'Max Pressure (PSI)': [None, None, None, None, None, None, None, 1000, 1000, 1000, 7500, 1000, 1000, None, None, None],
   'TC Offset (K)': [None, None, None, None, None, None, None, None, None, None, None, None, None, 0, 0, 0],
   'TC Type': [None, None, None, None, None, None, None, None, None, None, None, None, None, 'K', 'K', 'K']
}

@pytest.mark.instrument
class TestInstrument:
    def test_process_source(self):
        name1 = "https://docs.google.com/spreadsheets/d/11tinRex1---KHDVqnKRJ594H_LdEggauWd7tlRtDXoU/edit#gid=0"
        name2 = "https://docs.google.com/spreadsheets/d/1dzsvaEYkrfSZx0XB5U8f4lLKyWey5M1bJlnxP_EcodI/edit#gid=0"
        name3 = "Auto Instrumentation Sheet"
        name4 = "Miscellaneous and Vague Google Sheet"
        name5 = "/Users/evanhekman/mcnugget/excel_file.xlsx"
        name6 = "/Users/special_google_sheet.xlsx"
        name7 = "/Users/docs.google/edge case.xlsx"
        name8 = "C:\\Windows\\System\\excel.xlsx"
        name9 = "C:\\Google Docs\\WindowsExcelFile.xlsx"
        assert process_source(name1) == "url"
        assert process_source(name2) == "url"
        assert process_source(name3) == "name"
        assert process_source(name4) == "name"
        assert process_source(name5) == "filepath"
        assert process_source(name6) == "filepath"
        assert process_source(name7) == "filepath"
        assert process_source(name8) == "filepath"
        assert process_source(name9) == "filepath"
        print("test_process_sheet_name passed")

    def test_create_device_channels(self):
        create_device_channels(ctx)
        assert ctx.indexes["gse_ai"]
        assert ctx.indexes["gse_di"]
        create_device_channels(ctx)
        print("test_create_device_channels passed")

    # def test_process_row_vlv(self):
    #     process_valve(ctx, 0, test_df[0], )
    #     print("test_process_row passed for VLV")
    #
    # def test_process_row_pt(self):
    #     process_pt()
    #     print("test_process_row passed for VLV")
    #
    # def test_process_row_tc(self):
    #     process_tc()
    #     print("test_process_row passed for VLV")