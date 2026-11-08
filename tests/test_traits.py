import polars as pl
import pytest

import cas.traits
from cas.traits import filter_by_packs, load_aspirations, load_traits, load_worlds, pack_options


class TestCleaning:
    """Run the loaders on small made-up CSVs."""

    def test_traits_keeps_only_cas_personality_traits(self, monkeypatch, tmp_path):
        path = tmp_path / "traits.csv"
        path.write_text(
            "trait,description,section,category,pack\n"
            "Brave,Not scared,Personality,Emotional,Base Game\n"
            "Shy,Quiet,Personality,Social,Spa Day\n"
            "Wild,Toddler only,Personality,Toddler,Base Game\n"
            "Gym Rat,Bought with points,Reward,Satisfaction Reward,Base Game\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(cas.traits, "TRAITS_PATH", path)

        traits = load_traits()

        assert traits.columns == ["Trait", "Description", "Category", "Pack"]
        assert traits.rows() == [
            ("Brave", "Not scared", "Emotional", "Base Game"),
            ("Shy", "Quiet", "Social", "Spa Day"),
        ]

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
            "Pack",
        ]
        assert aspirations.row(0) == ("Chef", "Cook things", "Tasty", "Makes food better", "Base Game")

    def test_worlds_are_renamed_and_sorted(self, monkeypatch, tmp_path):
        path = tmp_path / "worlds.csv"
        path.write_text("world,pack\nWillow Creek,Base Game\nBrindleton Bay,Cats & Dogs\n", encoding="utf-8")
        monkeypatch.setattr(cas.traits, "WORLDS_PATH", path)

        worlds = load_worlds()

        assert worlds.columns == ["World", "Pack"]
        assert worlds["World"].to_list() == ["Brindleton Bay", "Willow Creek"]


class TestPackFilter:
    FRAME = pl.DataFrame({
        "Name": ["Base", "Spa", "Multi", "Seasons"],
        "Pack": ["Base Game", "Spa Day", "City Living; Snowy Escape", "Seasons"],
    })

    def names(self, packs):
        return filter_by_packs(self.FRAME, packs)["Name"].to_list()

    def test_no_packs_means_no_filter(self):
        assert self.names([]) == ["Base", "Spa", "Multi", "Seasons"]
        assert self.names(None) == ["Base", "Spa", "Multi", "Seasons"]

    def test_base_game_is_always_owned(self):
        assert self.names(["Spa Day"]) == ["Base", "Spa"]

    def test_any_one_of_several_packs_is_enough(self):
        assert self.names(["Snowy Escape"]) == ["Base", "Multi"]

    def test_options_split_multi_pack_cells_and_skip_the_base_game(self):
        assert pack_options(self.FRAME) == ["City Living", "Seasons", "Snowy Escape", "Spa Day"]


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
        assert load_traits().null_count().row(0) == (0, 0, 0, 0)

    def test_traits_cover_every_cas_category(self):
        assert set(load_traits()["Category"]) == set(cas.traits.CAS_TRAIT_CATEGORIES)

    def test_trait_names_are_clean(self):
        assert not load_traits()["Trait"].str.contains(r"\[n \d+\]|^&").any()

    def test_aspirations_have_no_missing_values(self):
        assert load_aspirations().null_count().row(0) == (0, 0, 0, 0, 0)
