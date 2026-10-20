from api.utils.group_names import NAME_MAX, unique_name


def test_blank_name_gets_a_generated_one():
    assert unique_name(None, []).strip() != ""
    assert unique_name("   ", []).strip() != ""


def test_free_name_is_kept_trimmed():
    assert unique_name("  Sam ", ["Alex"]) == "Sam"


def test_clash_gets_a_numeric_suffix_ignoring_case():
    assert unique_name("sam", ["Sam"]) == "sam 2"
    assert unique_name("Sam", ["Sam", "Sam 2"]) == "Sam 3"


def test_suffix_still_fits_the_column():
    long = "x" * NAME_MAX
    name = unique_name(long, [long])
    assert len(name) == NAME_MAX
    assert name.endswith(" 2")
