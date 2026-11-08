from pathlib import Path

import polars as pl
import streamlit as st

BASE_GAME = "Base Game"
PACK_SEPARATOR = "; "  # some traits come with any of several packs

TRAITS_PATH = Path(__file__).parent / "data" / "traits.csv"
ASPIRATIONS_PATH = Path(__file__).parent / "data" / "aspirations.csv"
WORLDS_PATH = Path(__file__).parent / "data" / "worlds.csv"


# traits.csv holds every trait on the wiki (bonus, reward, toddler...); only these can be picked in CAS.
CAS_TRAIT_CATEGORIES = ["Emotional", "Hobby", "Lifestyle", "Social"]


@st.cache_data
def load_traits() -> pl.DataFrame:
    return pl.read_csv(TRAITS_PATH).filter(
        (pl.col("section") == "Personality")
        & pl.col("category").is_in(CAS_TRAIT_CATEGORIES)
    ).select(
        pl.col("trait").alias("Trait"),
        pl.col("description").alias("Description"),
        pl.col("category").alias("Category"),
        pl.col("pack").alias("Pack"),
    )

@st.cache_data
def load_aspirations() -> pl.DataFrame:
    return pl.read_csv(
        ASPIRATIONS_PATH
    ).select(
        [
            "aspiration",
            "description",
            "reward_trait",
            "reward_trait_description",
            "pack",
        ]
    ).rename(
        {
        "aspiration" : "Aspiration",
        "description" : "Description",
        "reward_trait" : "Reward trait",
        "reward_trait_description" : "Reward trait description",
        "pack" : "Pack",
        }
    )

@st.cache_data
def load_worlds() -> pl.DataFrame:
    return pl.read_csv(WORLDS_PATH).rename(
        {"world": "World", "pack": "Pack"}
    ).sort("World")


def pack_options(*frames: pl.DataFrame) -> list[str]:
    """Every pack named in the frames' Pack columns, except the base game."""
    packs = {pack for df in frames for cell in df["Pack"] for pack in cell.split(PACK_SEPARATOR)}
    packs.discard(BASE_GAME)
    return sorted(packs)


def filter_by_packs(df: pl.DataFrame, packs: list[str] | None) -> pl.DataFrame:
    """Keep rows available with the given packs. The base game is always owned; no packs means no filter."""
    if not packs:
        return df
    owned = [*packs, BASE_GAME]
    return df.filter(
        pl.col("Pack").str.split(PACK_SEPARATOR).list.eval(pl.element().is_in(owned)).list.any()
    )