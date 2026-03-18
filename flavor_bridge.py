# ----------------------------
# DATA
# ----------------------------

import json
import streamlit as st

def normalize_pairings(data):
    all_pairs = {}

    for name, info in data.items():
        for paired, score in info["pairings"].items():
            if paired not in data:
                continue
            key = tuple(sorted([name, paired]))
            if key not in all_pairs:
                all_pairs[key] = []
            all_pairs[key].append(score)

    for (a, b), scores in all_pairs.items():
        avg = round(sum(scores) / len(scores), 2)
        data[a]["pairings"][b] = avg
        data[b]["pairings"][a] = avg

    return data


@st.cache_data
def load_ingredients():
    with open("ingredients.json", "r") as f:
        data = json.load(f)
    return normalize_pairings(data)

ingredients = load_ingredients()

ingredient_names = sorted(ingredients.keys())


# ----------------------------
# LOGIC
# ----------------------------

def matches_palette(ingredient_data, palette):
    if palette == "any":
        return True
    return palette in ingredient_data["taste"]


def find_keystones(a, b, data, palette, limit=15):
    a_pairs = data[a]["pairings"]
    b_pairs = data[b]["pairings"]

    results = []

    for ingredient in a_pairs:
        if ingredient in b_pairs and ingredient in data:
            score = (a_pairs[ingredient] + b_pairs[ingredient]) / 2

            if not matches_palette(data[ingredient], palette):
                continue

            results.append((ingredient, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]

@st.cache_data
def cached_find_keystones(a, b, palette):
    return find_keystones(a, b, ingredients, palette)


def check_foundation(a, b, data):
    if b in data[a]["pairings"]:
        return data[a]["pairings"][b]
    return None


def bond_label(score):
    if score >= 0.8:
        return "Structural"
    if score >= 0.6:
        return "Reinforced"
    if score >= 0.4:
        return "Experimental"
    return "Speculative"


def explain_keystone(a, b, keystone, data, score):
    tastes = ", ".join(data[keystone]["taste"])
    label = bond_label(score)

    return (
        f"**{keystone.capitalize()}** acts as the keystone between "
        f"**{a}** and **{b}** — bond strength {round(score, 2)} ({label}). "
        f"It brings a {tastes} dimension that anchors the composition."
    )

# ----------------------------
# UI
# ----------------------------

st.set_page_config(page_title="Studio Culinar-E", layout="centered")

st.title("Studio Culinar-E")
st.caption("Engineer Bold Compositions and Spread Culture. by Studio Monk-E.")

tab_blueprint, tab_archive = st.tabs(["The Blueprint", "Pantry Archive"])

with tab_blueprint:
    st.markdown("Select two ingredients and draft a blueprint, constructing a bridge between them.")

    col1, col2 = st.columns(2)
    with col1:
        ingredient_a = st.selectbox("Material A", ingredient_names, key="bridge_a")
    with col2:
        ingredient_b = st.selectbox("Material B", ingredient_names, key="bridge_b")

    palette = st.selectbox(
        "Flavor palette",
        ["any", "sweet", "savoury", "umami", "acidic", "fresh", "spicy", "bitter"],
        key="bridge_palette"
    )

    if st.button("Draft Blueprint"):
        if ingredient_a == ingredient_b:
            st.warning("Select two different materials to draft a blueprint.")
        else:
            # Foundation check
            foundation_score = check_foundation(ingredient_a, ingredient_b, ingredients)
            if foundation_score is not None:
                label = bond_label(foundation_score)
                st.subheader("Foundation")
                st.success(
                    f"**{ingredient_a.capitalize()}** and **{ingredient_b.capitalize()}** "
                    f"share a direct bond — strength {round(foundation_score, 2)} ({label}). "
                    f"Profiles: {', '.join(ingredients[ingredient_a]['taste'])} "
                    f"+ {', '.join(ingredients[ingredient_b]['taste'])}."
                )
                st.markdown("---")

            # Keystone search
            results = cached_find_keystones(
                ingredient_a,
                ingredient_b,
                palette
            )

            if not results:
                if foundation_score is not None:
                    st.info("No additional keystones found. The foundation above is solid on its own.")
                else:
                    st.info(
                        "No keystones found for this composition. "
                        "Try shifting the palette or selecting different materials."
                    )
            else:
                header = "Keystones to reinforce the structure" if foundation_score else "Keystones"
                st.subheader(header)
                for ingredient, score in results:
                    label = bond_label(score)
                    st.markdown(f"### {ingredient.capitalize()} — {round(score, 2)} ({label})")
                    st.write(
                        explain_keystone(
                            ingredient_a,
                            ingredient_b,
                            ingredient,
                            ingredients,
                            score
                        )
                    )

with tab_archive:
    st.markdown("Explore single ingredients and discover their connections.")

    selected = st.selectbox("Select material", ingredient_names, key="lookup_ingredient")

    if selected:
        meta = ingredients[selected]
        st.markdown(
            f"**Category:** {meta['type']} · "
            f"**Profile:** {', '.join(meta['taste'])} · "
            f"**Diet:** {', '.join(meta['diet']) if meta['diet'] else 'unrestricted'}"
        )

        st.markdown("---")

        pairs = meta["pairings"]
        sorted_pairs = sorted(pairs.items(), key=lambda x: x[1], reverse=True)

        for paired, score in sorted_pairs:
            label = bond_label(score)
            taste_info = ""
            if paired in ingredients:
                taste_info = f" · {', '.join(ingredients[paired]['taste'])}"
            st.markdown(f"**{paired.capitalize()}** — {round(score, 2)} ({label}){taste_info}")
