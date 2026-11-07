import json
import polars as pl
from itertools import zip_longest

import streamlit as st

from cas.sim_image import IMAGE_KEY, sim_image_input
from cas.sim_store import list_saved_sims, load_sim, save_sim, sim_exists
from cas.traits import load_traits, load_aspirations, load_worlds

from cas.ai import write_backstory, refine_backstory, pick_traits_and_aspiration

class sim:
    def __init__(self):
        self.first_name = None
        self.surname = None
        self.dob = None
        self.hometown = None
        self.image = None
        self.traits = None
        self.aspiration = None
        self.bonus_trait = None
        self.backstory = None

sim = sim()


def load_selected_sim():
    saved = load_sim(st.session_state["sim_to_load"])
    for field in ("first_name", "surname", "dob", "hometown", "traits", "aspiration", "backstory"):
        st.session_state[field] = saved[field]

    if saved["image"]:
        st.session_state[IMAGE_KEY] = saved["image"]
    else:
        st.session_state.pop(IMAGE_KEY, None)

    st.session_state.pop("pick_message", None)


def pick_from_backstory():
    """Fill in the traits and aspiration from the user's own backstory.

    This runs as a button callback, because Streamlit only lets widget values be
    changed before the widgets are drawn.
    """
    backstory = st.session_state.get("own_backstory", "").strip()
    if not backstory:
        st.session_state["pick_message"] = ("warning", "Write a backstory first.")
        return

    traits, aspirations = load_traits(), load_aspirations()
    try:
        picks = pick_traits_and_aspiration(
            backstory,
            traits=dict(zip(traits["Trait"], traits["Description"])),
            aspirations=dict(zip(aspirations["Aspiration"], aspirations["Description"])),
        )
    except RuntimeError as e:
        st.session_state["pick_message"] = ("error", f"Couldn't pick traits: {e}")
        return

    st.session_state["traits"] = picks["traits"]
    st.session_state["aspiration"] = picks["aspiration"]
    st.session_state["backstory"] = backstory
    st.session_state["pick_message"] = ("info", picks["reasoning"])


if saved_name := st.session_state.pop("saved_sim_name", None):
    st.toast(f"{saved_name} saved!")

st.title("Create a sim")
profile_details, profile_image = st.columns(2)


with st.sidebar:
    st.title("Basic sim info")
    sim.image = sim_image_input()
    sim.first_name = st.text_input("First name", key="first_name")
    sim.surname = st.text_input("Surname", key="surname")
    sim.dob = st.date_input("DOB",format="DD/MM/YYYY",min_value="1900-01-01", key="dob")
    sim.hometown = st.selectbox("Hometown", load_worlds()["World"].to_list(), index=None, key="hometown")
    save = st.button("Save sim")

    st.divider()
    sim_to_load = st.selectbox("Saved sims", list_saved_sims(), index=None, key="sim_to_load")
    st.button("Load sim", on_click=load_selected_sim, disabled=sim_to_load is None)

profile_details.header(f"{sim.first_name} {sim.surname}".strip() or "New sim")
profile_details.write(f"DOB: {sim.dob.strftime('%d/%m/%y')}" or None)
profile_details.write(f"Hometown: {sim.hometown}" or None)
if sim.image:
    profile_image.image(sim.image, width="stretch", alt="Sim image")

with st.expander("Start from your own backstory"):
    st.text_area("Your backstory", key="own_backstory", height=200)
    st.button("Pick traits and aspiration", on_click=pick_from_backstory)
    if pick_message := st.session_state.get("pick_message"):
        kind, text = pick_message
        getattr(st, kind)(text)

st.header("Traits")
traits = load_traits()
with st.expander("View all traits"):
    st.dataframe(traits)
sim.traits = st.multiselect("Select traits for your sim", traits["Trait"].to_list(), max_selections=3,help=None, key="traits")
descriptions = dict(zip(traits["Trait"], traits["Description"]))

for col, trait in zip_longest(st.columns(3), sim.traits):
    tile = col.container(height=250)
    if trait:
        tile.subheader(trait)
        tile.write(descriptions[trait]
        )

st.header("Aspiration")
aspirations = load_aspirations()
with st.expander("View all aspirations"):
    st.dataframe(aspirations)

sim.aspiration = st.selectbox("Select an aspiration for your sim", aspirations["Aspiration"].to_list(), index=None, key="aspiration")
aspirations_by_name = {row["Aspiration"]: row for row in aspirations.iter_rows(named=True)}

aspiration_tile, bonus_trait_tile = (col.container(height=250) for col in st.columns(2))
if sim.aspiration:
    aspiration = aspirations_by_name[sim.aspiration]
    sim.bonus_trait = aspiration["Reward trait"]

    aspiration_tile.subheader(sim.aspiration)
    aspiration_tile.write(aspiration["Description"])

    bonus_trait_tile.subheader(f"Bonus trait: {sim.bonus_trait}")
    bonus_trait_tile.write(
        aspiration["Reward trait description"].replace("[Sim first name]", sim.first_name or "This Sim")
    )


def add_descriptions_to_sim(sim, all_traits: pl.DataFrame = traits, all_aspirations: pl.DataFrame = aspirations):
    sim_data = {key: value for key, value in vars(sim).items() if key not in ("image", "backstory")}

    traits = {}
    for trait in sim_data["traits"]:
        traits[trait] = all_traits.filter(
            pl.col("Trait") == trait
        ).select(
            "Description"
        )[0].item()

    sim_data["traits"] = traits

    if sim_data["aspiration"]:
        aspiration = all_aspirations.filter(
            pl.col("Aspiration") == sim_data["aspiration"]
        ).row(0, named=True)

        sim_data["aspiration"] = {sim_data["aspiration"]: aspiration["Description"]}
        sim_data["bonus_trait"] = {
            aspiration["Reward trait"]: aspiration["Reward trait description"].replace(
                "[Sim first name]", sim_data["first_name"] or "This Sim"
            )
        }

    return sim_data

language = st.selectbox("Backstory language", ["English", "Russian"])
button = st.button("Write backstory")
if button:
    if language != "English":
        selected_language = language
    else:
        selected_language = None    
    prompt = json.dumps(add_descriptions_to_sim(sim), default=str) 
    st.session_state["backstory"] = write_backstory(prompt, language=selected_language)

refine = st.text_area("Refine backstory")
refine_button = st.button("Submit")

if refine_button and refine and st.session_state.get("backstory"):
    st.session_state["backstory"] = refine_backstory(
        sim=json.dumps(add_descriptions_to_sim(sim), default=str),
        backstory=st.session_state["backstory"],
        language=None if language == "English" else language,
        prompt=refine,
    )
    
    
sim.backstory = st.session_state.get("backstory")
if sim.backstory:
    st.code(sim.backstory, language=None, wrap_lines=True)

@st.dialog("Save sim")
def save_box():
  if sim.image:
    st.image(sim.image)
  st.write(f"Name: {sim.first_name} {sim.surname}")
  st.write(f"DOB {sim.dob.strftime('%d/%m/%y')}")
  st.write(f"Hometown: {sim.hometown}")
  st.write(f"Traits: {" , ".join(sim.traits)}")
  st.write(f"Aspiration: {sim.aspiration}, Bonus trait: {sim.bonus_trait}")

  name = f"{sim.first_name} {sim.surname}".strip()
  if not name:
    st.warning("Give your sim a name before saving.")
  elif sim_exists(name):
    st.warning(f"This will replace the saved sim called {name}.")

  if st.button("Save", disabled=not name):
    save_sim(sim)
    st.session_state["saved_sim_name"] = name
    st.rerun()

if save:
    save_box()
   