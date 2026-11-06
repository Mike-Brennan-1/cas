import pytest

import cas.traits
from cas.traits import load_aspirations, load_traits, load_worlds


class TestCleaning:
    """Run the loaders on small made-up CSVs."""

    def test_traits_strips_footnotes_and_drops_pack(self, monkeypatch, tmp_path):
        path = tmp_path / "traits.csv"
        path.write_text("Brave [n 1],Not scared,&BG\nShy,Quiet,&GP01\n", encoding="utf-8")
        monkeypatch.setattr(cas.traits, "TRAITS_PATH", path)

        traits = load_traits()

        assert traits.columns == ["Trait", "Description"]
        assert traits["Trait"].to_list() == ["Brave", "Shy"]

    def test_aspirations_keeps_and_renames_the_columns_the_app_uses(self, monkeypatch, tmp_path):
        path = tmp_path / "aspirations.csv"
        path.write_text(
            "aspiration,description,category,reward_trait,reward_trait_description,pack\n"
            "Chef,Cook things,Food,Tasty,Makes food better,Base Game\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(cas.traits, "ASPIRATIONS_PATH", path)

        aspirations = load_aspirations()

        assert aspirations.columns == [
            "Aspiration",
            "Description",
            "Reward trait",
            "Reward trait description",
        ]
        assert aspirations.row(0) == ("Chef", "Cook things", "Tasty", "Makes food better")

    def test_worlds_are_renamed_and_sorted(self, monkeypatch, tmp_path):
        path = tmp_path / "worlds.csv"
        path.write_text("world,pack\nWillow Creek,Base Game\nBrindleton Bay,Cats & Dogs\n", encoding="utf-8")
        monkeypatch.setattr(cas.traits, "WORLDS_PATH", path)

        worlds = load_worlds()

        assert worlds.columns == ["World", "Pack"]
        assert worlds["World"].to_list() == ["Brindleton Bay", "Willow Creek"]


class TestShippedData:
    """Check the real CSVs. app.py relies on these values being present and unique."""

    @pytest.mark.parametrize(
        ("loader", "name_column"),
        [(load_traits, "Trait"), (load_aspirations, "Aspiration"), (load_worlds, "World")],
    )
    def test_names_are_unique(self, loader, name_column):
        names = loader()[name_column]

        assert names.len() > 0
        assert names.n_unique() == names.len()

    def test_traits_have_no_missing_values(self):
        assert load_traits().null_count().row(0) == (0, 0)

    def test_trait_names_are_clean(self):
        assert not load_traits()["Trait"].str.contains(r"\[n \d+\]|^&").any()

    def test_aspirations_have_no_missing_values(self):
        assert load_aspirations().null_count().row(0) == (0, 0, 0, 0)
