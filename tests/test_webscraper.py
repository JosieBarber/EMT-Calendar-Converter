import pytest
from datetime import datetime
from src.webscraper import scrape_schedule, fetch_html_content, extract_shift_details, extract_all_shifts


############################################################################
#                   TESTS FOR extract_shift_details()                      #
############################################################################

# Test for valid AM Third shift
def test_extract_shift_details_valid():
    result = extract_shift_details(
        "<td valign='top' id='shift_1_2026-03-03_14'><div class='cal_shift_row'> <a href='javascript:void(0)' class='cal_shift' title='AM Third EMT: Joseph H Dalen'><span>JHD</span></a> </div></td>"
    )

    assert isinstance(result, dict)
    assert "date" in result
    assert "time" in result
    assert "shift" in result
    assert "name" in result

    assert result["date"] == datetime(2026, 3, 3)
    assert result["time"] == "AM"
    assert result["shift"] == "Third"
    assert result["name"] == "Joseph"


# Test for valid PMSecond shift
def test_extract_shift_details_pm_second():
    result = extract_shift_details(
        "<td id='shift_1_2026-03-05_11'><div class='cal_shift_row'><a class='cal_shift' title='PM Second EMT: Alice Smith'></a></div></td>"
    )

    assert isinstance(result, dict)
    assert result["date"] == datetime(2026, 3, 5)
    assert result["time"] == "PM"
    assert result["shift"] == "Second"
    assert result["name"] == "Alice"


# Test for valid AM First shift
def test_extract_shift_details_am_first():
    result = extract_shift_details(
        "<td id='shift_1_2026-03-06_2'><div class='cal_shift_row'><a class='cal_shift' title='AM First EMT: Bob Johnson'></a></div></td>"
    )

    assert isinstance(result, dict)
    assert result["date"] == datetime(2026, 3, 6)
    assert result["time"] == "AM"
    assert result["shift"] == "First"
    assert result["name"] == "Bob"


# Test for unknown shift number (fallback behavior)
def test_extract_shift_details_unknown_shift():
    result = extract_shift_details(
        "<td id='shift_1_2026-03-07_99'><div class='cal_shift_row'><a class='cal_shift' title='AM Mystery EMT: Carl Adams'></a></div></td>"
    )

    assert isinstance(result, dict)
    assert result["date"] == datetime(2026, 3, 7)
    assert result["time"] == "Unknown"
    assert result["shift"] == "Unknown"
    assert result["name"] == "Carl"


# Test for missing EMT name in title
def test_extract_shift_details_missing_name():
    result = extract_shift_details(
        "<td id='shift_1_2026-03-08_14'><div class='cal_shift_row'><a class='cal_shift' title='AM Third'></a></div></td>"
    )

    assert isinstance(result, dict)
    assert result["date"] == datetime(2026, 3, 8)
    assert result["time"] == "AM"
    assert result["shift"] == "Third"
    assert result["name"] == "Unknown"


# Test for missing ID attribute (should return None)
def test_extract_shift_details_missing_id():
    result = extract_shift_details(
        "<td valign='top'><div class='cal_shift_row'><a class='cal_shift' title='AM Third EMT: Dana Lee'></a></div></td>"
    )

    assert result is None


# Test for completely empty cell
def test_extract_shift_details_empty_cell():
    result = extract_shift_details("<td></td>")
    assert result is None


# Test for extra whitespace in HTML
def test_extract_shift_details_extra_whitespace():
    result = extract_shift_details(
        "<td id='shift_1_2026-03-09_17'>  <div> <a class='cal_shift' title='PM Third EMT:   Evan Brown'></a> </div> </td>"
    )

    assert isinstance(result, dict)
    assert result["date"] == datetime(2026, 3, 9)
    assert result["time"] == "PM"
    assert result["shift"] == "Third"
    assert result["name"] == "Evan"


############################################################################
#                     TESTS FOR extract_all_shifts()                       #
############################################################################
# Test for single shift in table
def test_extract_all_shifts_single():
    html = """
    <table>
        <tr>
            <td valign="top" id="shift_1_2026-03-03_14">
                <div class="cal_shift_row">
                    <a class="cal_shift" title="AM Third EMT: Joseph H Dalen"></a>
                </div>
            </td>
        </tr>
    </table>
    """

    result = extract_all_shifts(html)

    assert isinstance(result, list)
    assert len(result) == 1

    shift = result[0]
    assert shift["date"] == datetime(2026, 3, 3)
    assert shift["time"] == "AM"
    assert shift["shift"] == "Third"
    assert shift["name"] == "Joseph"


# Test for multiple shifts in the same table row
def test_extract_all_shifts_multiple_same_row():
    html = """
    <table>
        <tr>
            <td id="shift_1_2026-03-03_14">
                <div><a class="cal_shift" title="AM Third EMT: Joseph H Dalen"></a></div>
            </td>
            <td id="shift_1_2026-03-04_11">
                <div><a class="cal_shift" title="PM Second EMT: Alice Smith"></a></div>
            </td>
            <td id="shift_1_2026-03-05_2">
                <div><a class="cal_shift" title="AM First EMT: Bob Johnson"></a></div>
            </td>
        </tr>
    </table>
    """

    result = extract_all_shifts(html)

    assert len(result) == 3
    names = {shift["name"] for shift in result}

    assert "Joseph" in names
    assert "Alice" in names
    assert "Bob" in names


# Test for multiple rows of shifts in a table
def test_extract_all_shifts_multiple_rows():
    html = """
    <table>
        <tr>
            <td id="shift_1_2026-03-03_14">
                <div><a class="cal_shift" title="AM Third EMT: Joseph H Dalen"></a></div>
            </td>
            <td id="shift_1_2026-03-04_11">
                <div><a class="cal_shift" title="PM Second EMT: Alice Smith"></a></div>
            </td>
        </tr>
        <tr>
            <td id="shift_1_2026-03-05_2">
                <div><a class="cal_shift" title="AM First EMT: Bob Johnson"></a></div>
            </td>
            <td id="shift_1_2026-03-06_17">
                <div><a class="cal_shift" title="PM Third EMT: Evan Brown"></a></div>
            </td>
        </tr>
    </table>
    """

    result = extract_all_shifts(html)

    assert len(result) == 4

    names = {shift["name"] for shift in result}

    assert names == {"Joseph", "Alice", "Bob", "Evan"}


# Test fo table with non-shift cells
def test_extract_all_shifts_ignores_non_shift_cells():
    html = """
    <table>
        <tr>
            <td id="header"></td>
            <td id="shift_1_2026-03-07_2">
                <div><a class="cal_shift" title="AM First EMT: Dana Lee"></a></div>
            </td>
            <td id="footer"></td>
        </tr>
    </table>
    """

    result = extract_all_shifts(html)

    assert len(result) == 1
    assert result[0]["name"] == "Dana"


# Test for table with no shifts
def test_extract_all_shifts_none():
    html = """
    <table>
        <tr>
            <td id="a"></td>
            <td id="b"></td>
        </tr>
    </table>
    """

    result = extract_all_shifts(html)

    assert isinstance(result, list)
    assert len(result) == 0


# Test for whitespace and formatting variations
def test_extract_all_shifts_whitespace():
    html = """
    <table>
        <tr>
            <td id="shift_1_2026-03-08_17">
                <div>
                    <a class="cal_shift"
                       title="PM Third EMT:   Frank Miller"></a>
                </div>
            </td>
        </tr>
    </table>
    """

    result = extract_all_shifts(html)

    assert len(result) == 1
    assert result[0]["name"] == "Frank"
    assert result[0]["shift"] == "Third"
    assert result[0]["time"] == "PM"
