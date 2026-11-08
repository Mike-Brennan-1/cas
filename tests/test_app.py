"""Run app.py through Streamlit's test harness, since its logic lives in the script."""
import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from openai import APIError
from unittest.mock import MagicMock
from streamlit.testing.v1 import AppTest

import cas
from cas.sim_image import IMAGE_KEY
from cas.sim_store import save_sim, sim_exists
from cas.traits import load_aspirations, load_traits

APP_PATH = str(Path(cas.__file__).parent / "app.py")


@pytest.fixture
def app():
    return AppTest.from_file(APP_PATH, default_timeout=30).run()


def button(app, label):
    return next(b for b in app.button if b.label == label)


def selectbox(app, label):
    return next(s for s in app.selectbox if s.label == label)


def assert_no_errors(app):
    assert not app.exception


def test_app_starts_with_a_blank_sim(app):
    assert_no_errors(app)
    assert app.header[0].value == "New sim"


def test_name_appears_in_the_profile_header(app):
    app.text_input(key="first_name").set_value("Terry")
    app.text_input(key="surname").set_value("Anderson").run()

    assert_no_errors(app)
    assert app.header[0].value == "Terry Anderson"


def test_every_aspiration_can_be_selected(app):
    for aspiration in load_aspirations()["Aspiration"]:
        app.selectbox(key="aspiration").set_value(aspiration).run()
        assert_no_errors(app)


def test_backstory_prompt_includes_descriptions(app, fake_openai):
    traits = load_traits()
    aspirations = load_aspirations()
    trait = traits.row(0, named=True)
    aspiration = aspirations.row(0, named=True)

    app.text_input(key="first_name").set_value("Terry")
    app.multiselect(key="traits").set_value([trait["Trait"]])
    app.selectbox(key="aspiration").set_value(aspiration["Aspiration"]).run()
    button(app, "Write backstory").click().run()

    assert_no_errors(app)
    prompt = fake_openai.call_args.kwargs["input"]
    sim_json = json.loads(prompt[prompt.index("{"):prompt.rindex("}") + 1])
    assert sim_json["traits"] == {trait["Trait"]: trait["Description"]}
    assert sim_json["aspiration"] == {aspiration["Aspiration"]: aspiration["Description"]}
    assert list(sim_json["bonus_trait"]) == [aspiration["Reward trait"]]


def test_backstory_works_with_nothing_selected(app, fake_openai):
    button(app, "Write backstory").click().run()

    assert_no_errors(app)
    fake_openai.assert_called_once()


def test_generated_backstory_is_shown(app):
    button(app, "Write backstory").click().run()

    assert [block.value for block in app.code] == ["A backstory"]


def test_english_sends_no_language_instruction(app, fake_openai):
    button(app, "Write backstory").click().run()

    assert "Write your entire response" not in fake_openai.call_args.kwargs["instructions"]


def test_russian_is_passed_to_the_model(app, fake_openai):
    selectbox(app, "Backstory language").set_value("Russian").run()
    button(app, "Write backstory").click().run()

    assert "Write your entire response in Russian" in fake_openai.call_args.kwargs["instructions"]


def test_picking_from_a_backstory_fills_in_the_form(app, fake_openai):
    fake_openai.return_value = SimpleNamespace(id="resp_1", output_text=json.dumps({
        "traits": ["Creative", "Genius"],
        "aspiration": "Bestselling Author",
        "reasoning": "Terry writes a lot.",
    }))

    app.text_area(key="own_backstory").set_value("Terry wrote novels every night.")
    button(app, "Pick traits and aspiration").click().run()

    assert_no_errors(app)
    assert app.multiselect(key="traits").value == ["Creative", "Genius"]
    assert app.selectbox(key="aspiration").value == "Bestselling Author"
    assert [block.value for block in app.code] == ["Terry wrote novels every night."]
    assert [info.value for info in app.info] == ["Terry writes a lot."]
    assert "Terry wrote novels every night." in fake_openai.call_args.kwargs["input"]


def test_picking_needs_a_backstory(app, fake_openai):
    button(app, "Pick traits and aspiration").click().run()

    assert_no_errors(app)
    fake_openai.assert_not_called()
    assert "Write a backstory first." in [w.value for w in app.warning]


def test_picking_shows_api_errors(app, fake_openai):
    fake_openai.side_effect = APIError("Service down", request=MagicMock(), body=None)

    app.text_area(key="own_backstory").set_value("Terry wrote novels every night.")
    button(app, "Pick traits and aspiration").click().run()

    assert_no_errors(app)
    assert app.multiselect(key="traits").value == []
    assert any("Service down" in e.value for e in app.error)


def test_loading_a_sim_fills_in_the_form(make_sim, png_bytes):
    save_sim(make_sim(image=png_bytes))
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()

    app.selectbox(key="sim_to_load").set_value("Terry Anderson").run()
    button(app, "Load sim").click().run()

    assert_no_errors(app)
    assert app.text_input(key="first_name").value == "Terry"
    assert app.selectbox(key="hometown").value == "Copperdale"
    assert app.multiselect(key="traits").value == ["Creative", "Genius"]
    assert app.selectbox(key="aspiration").value == "Bestselling Author"
    assert [block.value for block in app.code] == ["Once upon a time"]
    assert app.session_state[IMAGE_KEY] == png_bytes


def test_loading_a_sim_without_an_image_clears_the_current_one(make_sim, png_bytes):
    save_sim(make_sim())
    app = AppTest.from_file(APP_PATH, default_timeout=30)
    app.session_state[IMAGE_KEY] = png_bytes
    app.run()

    app.selectbox(key="sim_to_load").set_value("Terry Anderson").run()
    button(app, "Load sim").click().run()

    assert_no_errors(app)
    assert IMAGE_KEY not in app.session_state


def test_new_sim_clears_the_form(app):
    app.text_input(key="first_name").set_value("Terry")
    app.text_input(key="surname").set_value("Anderson")
    app.date_input(key="dob").set_value(date(1990, 11, 6))
    app.selectbox(key="hometown").set_value("Copperdale")
    app.text_area(key="own_backstory").set_value("Terry wrote novels every night.")
    app.multiselect(key="traits").set_value(["Creative", "Genius"])
    app.selectbox(key="aspiration").set_value("Bestselling Author").run()

    button(app, "New sim").click().run()

    assert_no_errors(app)
    assert app.text_input(key="first_name").value == ""
    assert app.text_input(key="surname").value == ""
    assert app.date_input(key="dob").value == date.today()
    assert app.selectbox(key="hometown").value is None
    assert app.selectbox(key="sim_to_load").value is None
    assert app.text_area(key="own_backstory").value == ""
    assert app.multiselect(key="traits").value == []
    assert app.selectbox(key="aspiration").value is None


def test_delete_removes_the_loaded_sim(make_sim):
    save_sim(make_sim())
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()

    app.selectbox(key="sim_to_load").set_value("Terry Anderson").run()
    button(app, "Load sim").click().run()
    button(app, "Delete Terry Anderson").click().run()

    assert_no_errors(app)
    assert not sim_exists("Terry Anderson")
    assert app.text_input(key="first_name").value == ""


def test_delete_is_disabled_for_a_new_sim_even_with_a_saved_sim_chosen(make_sim):
    save_sim(make_sim())
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()

    app.selectbox(key="sim_to_load").set_value("Terry Anderson").run()

    assert button(app, "Delete sim").disabled


def test_delete_ignores_a_different_sim_chosen_after_loading(make_sim):
    save_sim(make_sim())
    save_sim(make_sim(first_name="Mike", surname="Brennan"))
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()

    app.selectbox(key="sim_to_load").set_value("Terry Anderson").run()
    button(app, "Load sim").click().run()
    app.selectbox(key="sim_to_load").set_value("Mike Brennan").run()
    button(app, "Delete Terry Anderson").click().run()

    assert_no_errors(app)
    assert not sim_exists("Terry Anderson")
    assert sim_exists("Mike Brennan")


def test_load_button_is_disabled_until_a_sim_is_chosen(app):
    assert button(app, "Load sim").disabled


def test_remove_image_clears_it(png_bytes):
    app = AppTest.from_file(APP_PATH, default_timeout=30)
    app.session_state[IMAGE_KEY] = png_bytes
    app.run()

    button(app, "Remove image").click().run()

    assert_no_errors(app)
    assert IMAGE_KEY not in app.session_state


# AppTest can't click "Save" inside the dialog: it reruns the whole script rather
# than just the dialog, so the dialog closes first. test_sim_store.py covers saving.
def test_save_dialog_allows_saving_a_named_sim(app):
    app.text_input(key="first_name").set_value("Terry")
    app.text_input(key="surname").set_value("Anderson").run()

    button(app, "Save sim").click().run()

    assert_no_errors(app)
    assert not button(app, "Save").disabled


def test_save_dialog_requires_a_name(app):
    button(app, "Save sim").click().run()

    assert_no_errors(app)
    assert button(app, "Save").disabled
    assert "Give your sim a name before saving." in [w.value for w in app.warning]


def test_save_dialog_warns_before_overwriting(app, make_sim):
    save_sim(make_sim())
    app.text_input(key="first_name").set_value("Terry")
    app.text_input(key="surname").set_value("Anderson").run()

    button(app, "Save sim").click().run()

    assert "This will replace the saved sim called Terry Anderson." in [w.value for w in app.warning]
