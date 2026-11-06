import json
from datetime import date

import pytest

from cas.sim_store import list_saved_sims, load_sim, save_sim, sim_exists


def test_save_writes_json_without_the_image(make_sim, sims_dir, png_bytes):
    save_sim(make_sim(image=png_bytes))

    saved = json.loads((sims_dir / "terry_anderson.json").read_text(encoding="utf-8"))

    assert "image" not in saved
    assert saved["first_name"] == "Terry"
    assert saved["dob"] == "1990-11-06"


def test_save_writes_the_image_alongside_the_json(make_sim, sims_dir, png_bytes):
    save_sim(make_sim(image=png_bytes))

    assert (sims_dir / "terry_anderson.image").read_bytes() == png_bytes


def test_save_without_an_image_writes_no_image_file(make_sim, sims_dir):
    save_sim(make_sim())

    assert not (sims_dir / "terry_anderson.image").exists()


def test_resaving_without_an_image_removes_the_old_one(make_sim, sims_dir, png_bytes):
    save_sim(make_sim(image=png_bytes))
    save_sim(make_sim(image=None))

    assert not (sims_dir / "terry_anderson.image").exists()


def test_resaving_replaces_the_existing_sim(make_sim, sims_dir):
    save_sim(make_sim(hometown="Copperdale"))
    save_sim(make_sim(hometown="Willow Creek"))

    assert load_sim("Terry Anderson")["hometown"] == "Willow Creek"
    assert len(list(sims_dir.glob("*.json"))) == 1


def test_save_creates_a_missing_sims_folder(make_sim, sims_dir):
    sims_dir.rmdir()

    save_sim(make_sim())

    assert sim_exists("Terry Anderson")


def test_load_restores_every_field(make_sim, png_bytes):
    sim = make_sim(image=png_bytes)
    save_sim(sim)

    assert load_sim("Terry Anderson") == vars(sim)


def test_load_returns_dob_as_a_date(make_sim):
    save_sim(make_sim())

    assert load_sim("Terry Anderson")["dob"] == date(1990, 11, 6)


def test_load_returns_no_image_when_there_is_none(make_sim):
    save_sim(make_sim())

    assert load_sim("Terry Anderson")["image"] is None


def test_non_english_text_survives_a_round_trip(make_sim):
    save_sim(make_sim(first_name="Дмитрий", surname="Иванов", backstory="Жил-был Сим"))

    loaded = load_sim("Дмитрий Иванов")

    assert loaded["first_name"] == "Дмитрий"
    assert loaded["backstory"] == "Жил-был Сим"


def test_load_of_an_unknown_sim_raises():
    with pytest.raises(FileNotFoundError):
        load_sim("Nobody Here")


def test_sim_exists_is_false_before_saving():
    assert not sim_exists("Terry Anderson")


@pytest.mark.parametrize("name", ["Terry Anderson", "terry anderson", "  TERRY   ANDERSON  "])
def test_sim_exists_ignores_case_and_extra_spaces(make_sim, name):
    save_sim(make_sim())

    assert sim_exists(name)


def test_list_is_empty_with_no_saved_sims():
    assert list_saved_sims() == []


def test_list_returns_full_names_in_order(make_sim):
    save_sim(make_sim(first_name="Zed", surname="Young"))
    save_sim(make_sim(first_name="Amy", surname="Stone"))

    assert list_saved_sims() == ["Amy Stone", "Zed Young"]


def test_list_handles_a_sim_with_no_surname(make_sim):
    save_sim(make_sim(surname=""))

    assert list_saved_sims() == ["Terry"]


def test_names_cannot_write_outside_the_sims_folder(make_sim, sims_dir):
    save_sim(make_sim(first_name="../../evil", surname="name"))

    assert [path.parent for path in sims_dir.parent.rglob("*.json")] == [sims_dir]
