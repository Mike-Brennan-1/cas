from pathlib import Path

import polars as pl
import streamlit as st

TRAITS_PATH = Path(__file__).parent / "data" / "traits.csv"
ASPIRATIONS_PATH = Path(__file__).parent / "data" / "aspirations.csv"
WORLDS_PATH = Path(__file__).parent / "data" / "worlds.csv"


@st.cache_data
def load_traits() -> pl.DataFrame:
    return pl.read_csv(
        TRAITS_PATH,
        has_header=False,
        new_columns=["Trait", "Description", "pack"],
    ).with_columns(
        pl.col("Trait", "pack")
        .str.replace(r"\s*\[n \d+\]", "")
        .str.strip_prefix("&")
    ).drop("pack")

@st.cache_data
def load_aspirations() -> pl.DataFrame:
    return pl.read_csv(
        ASPIRATIONS_PATH
    ).select(
        [
            "aspiration",
            "description",
            "reward_trait",
            "reward_trait_description"
        ]
    ).rename(
        {
        "aspiration" : "Aspiration",
        "description" : "Description",
        "reward_trait" : "Reward trait",
        "reward_trait_description" : "Reward trait description"
        }
    )

@st.cache_data
def load_worlds() -> pl.DataFrame:
    return pl.read_csv(WORLDS_PATH).rename(
        {"world": "World", "pack": "Pack"}
    ).sort("World")