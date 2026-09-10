
import pandas as pd
import streamlit as st
from datetime import date

st.set_page_configst.markdown("""
<style>

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

h1 {
    font-size: 3rem !important;
    font-weight: 700 !important;
    letter-spacing: -1px;
}

h2, h3 {
    font-weight: 600 !important;
}

[data-testid="stMetric"] {
    background: white;
    border-radius: 16px;
    padding: 18px;
    border: 1px solid #E2E2E2;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}

[data-testid="stSidebar"] {
    border-right: 1px solid #E0E0E0;
}

.stButton > button {
    border-radius: 12px;
    padding: 0.65rem 1.2rem;
    font-weight: 600;
}

[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}

div[data-testid="stExpander"] {
    border-radius: 12px;
    border: 1px solid #E1E1E1;
}

</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv("data/destinations.csv")

df = load_data()

def inverse_score(value, low, high):
    if high == low:
        return 100.0
    return max(0.0, min(100.0, 100 * (high - value) / (high - low)))

def weather_score(avg_temp_f, rain_days, preferred_low, preferred_high):
    if preferred_low <= avg_temp_f <= preferred_high:
        temp = 100
    else:
        d = min(abs(avg_temp_f - preferred_low), abs(avg_temp_f - preferred_high))
        temp = max(0, 100 - 7 * d)
    rain = max(0, 100 - 8 * rain_days)
    return 0.75 * temp + 0.25 * rain

def budget_score(cost, budget):
    if cost <= budget:
        return min(100, 85 + (1 - cost / budget) * 30)
    over = (cost - budget) / budget
    return max(0, 80 - over * 180)

def interest_score(row, weights):
    vals = {
        "Nature": row["nature_score"],
        "Food": row["food_score"],
        "History": row["history_score"],
        "Nightlife": row["nightlife_score"],
        "Beach": row["beach_score"],
    }
    total = sum(weights.values()) or 1
    return sum(vals[k] * weights[k] for k in vals) / total

def explanation(row, budget, max_flight, weights):
    strengths = []
    for label, col in [
        ("nature/scenery", "nature_score"),
        ("food", "food_score"),
        ("history/culture", "history_score"),
        ("nightlife", "nightlife_score"),
        ("beaches", "beach_score"),
    ]:
        if row[col] >= 85:
            strengths.append(label)

    reasons = ", ".join(strengths[:3]) if strengths else "its overall balance"

    tradeoffs = []
    if row["estimated_trip_cost"] > budget:
        tradeoffs.append("estimated trip cost is above your budget")
    if row["flight_hours"] > max_flight:
        tradeoffs.append("travel time exceeds your preferred maximum")
    if row["rain_days"] >= 4:
        tradeoffs.append("the season can be relatively rainy")
    if row["beach_score"] < 50 and weights["Beach"] >= 7:
        tradeoffs.append("it is not a strong beach destination")
    if row["nightlife_score"] < 50 and weights["Nightlife"] >= 7:
        tradeoffs.append("nightlife is weaker than you prefer")

    tradeoff = tradeoffs[0] if tradeoffs else "there are no major mismatches with your current preferences"
    return (
        f"{row['city']} performs well because of {reasons}. "
        f"The estimated total trip cost is about ${row['estimated_trip_cost']:,.0f}, "
        f"and travel time is about {row['flight_hours']:.1f} hours from Philadelphia. "
        f"The main trade-off is that {tradeoff}."
    )

st.sidebar.titlest.sidebar.title("Plan Your Trip ✈️")
st.sidebar.caption("Tell us what your ideal vacation looks like.")
departure = st.sidebar.selectbox("Departure airport", ["PHL"])
start_date = st.sidebar.date_input("Departure date", date(2027, 6, 13))
end_date = st.sidebar.date_input("Return date", date(2027, 6, 20))
budget = st.sidebar.slider("Total trip budget", 1000, 7000, 2500, 100)
max_flight = st.sidebar.slider("Preferred maximum travel time (hours)", 4, 18, 10)
preferred_low = st.sidebar.slider("Preferred daytime temp — low °F", 45, 80, 65)
preferred_high = st.sidebar.slider("Preferred daytime temp — high °F", 60, 95, 80)

st.sidebar.markdown("### What matters most?")
weights = {
    "Nature": st.sidebar.slider("Nature / scenery", 0, 10, 10),
    "Food": st.sidebar.slider("Food", 0, 10, 8),
    "History": st.sidebar.slider("History / culture", 0, 10, 7),
    "Nightlife": st.sidebar.slider("Nightlife", 0, 10, 3),
    "Beach": st.sidebar.slider("Beach", 0, 10, 2),
}

nights = max(1, (end_date - start_date).days)
scored = df.copy()

scored["estimated_trip_cost"] = (
    scored["sample_roundtrip_flight"]
    + nights * scored["hotel_per_night"]
    + (nights + 1) * scored["daily_food"]
    + (nights + 1) * scored["daily_transit"]
    + (nights + 1) * scored["daily_activities"]
)

fmin, fmax = scored["sample_roundtrip_flight"].min(), scored["sample_roundtrip_flight"].max()
tmin, tmax = scored["flight_hours"].min(), scored["flight_hours"].max()

scored["flight_cost_score"] = scored["sample_roundtrip_flight"].apply(lambda x: inverse_score(x, fmin, fmax))
scored["flight_time_score"] = scored["flight_hours"].apply(lambda x: inverse_score(x, tmin, tmax))
scored["weather_match_score"] = scored.apply(
    lambda r: weather_score(r["avg_temp_f"], r["rain_days"], preferred_low, preferred_high), axis=1
)
scored["budget_match_score"] = scored["estimated_trip_cost"].apply(lambda x: budget_score(x, budget))
scored["interest_match_score"] = scored.apply(lambda r: interest_score(r, weights), axis=1)

scored["overall_score"] = (
    0.35 * scored["interest_match_score"]
    + 0.25 * scored["budget_match_score"]
    + 0.15 * scored["weather_match_score"]
    + 0.15 * scored["flight_cost_score"]
    + 0.10 * scored["flight_time_score"]
)

scored.loc[scored["flight_hours"] > max_flight, "overall_score"] -= (
    scored["flight_hours"] - max_flight
) * 2.5

scored["overall_score"] = scored["overall_score"].clip(0, 100).round(1)
scored = scored.sort_values("overall_score", ascending=False).reset_index(drop=True)

st.titlest.title("Where Should You Go Next? ✈️")
st.markdown(
    "Personalized destination recommendations based on your budget, travel style, weather preferences, and interests."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Trip length", f"{nights} nights")
c2.metric("Budget", f"${budget:,}")
c3.metric("Destinations", len(scored))
c4.metric("Top match", f"{scored.iloc[0]['overall_score']:.1f}%")

st.divider()

top = scored.iloc[0]
st.subheader(f"🥇 Best Match: {top['city']}, {top['country']}")

a, b, c, d = st.columns(4)
a.metric("Match score", f"{top['overall_score']:.1f}%")
b.metric("Est. trip cost", f"${top['estimated_trip_cost']:,.0f}")
c.metric("Sample airfare", f"${top['sample_roundtrip_flight']:,.0f}")
d.metric("Travel time", f"{top['flight_hours']:.1f} hrs")

st.info(explanation(top, budget, max_flight, weights))

st.markdown("### Top 5 destinations")
table = scored.head(5)[
    ["city", "country", "overall_score", "estimated_trip_cost", "avg_temp_f", "flight_hours", "interest_match_score"]
].copy()
table.columns = ["Destination", "Country", "Match %", "Est. Trip Cost", "Avg Temp °F", "Travel Hours", "Interest Fit"]
table["Est. Trip Cost"] = table["Est. Trip Cost"].map(lambda x: f"${x:,.0f}")
table["Interest Fit"] = table["Interest Fit"].round(1)
st.dataframe(table, hide_index=True, use_container_width=True)

st.markdown("### Top 10 ranking")
st.bar_chart(scored.head(10).set_index("city")[["overall_score"]])

st.markdown("### Explore a destination")
selected = st.selectbox("Destination", scored["city"].tolist())
sel = scored[scored["city"] == selected].iloc[0]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Budget fit", f"{sel['budget_match_score']:.0f}")
m2.metric("Weather fit", f"{sel['weather_match_score']:.0f}")
m3.metric("Interest fit", f"{sel['interest_match_score']:.0f}")
m4.metric("Flight-price fit", f"{sel['flight_cost_score']:.0f}")
m5.metric("Travel-time fit", f"{sel['flight_time_score']:.0f}")

st.write(explanation(sel, budget, max_flight, weights))

with st.expander("Destination interest profile"):
    p = pd.DataFrame({
        "Category": ["Nature", "Food", "History", "Nightlife", "Beach"],
        "Destination Score": [
            sel["nature_score"], sel["food_score"], sel["history_score"],
            sel["nightlife_score"], sel["beach_score"]
        ]
    })
    st.dataframe(p, hide_index=True, use_container_width=True)

with st.expander("How the model works"):
    st.markdown("""
**Inputs:** budget, trip length, maximum preferred travel time, weather preferences, and traveler interests.

**Normalization:** airfare, travel time, budget fit, weather, and interest characteristics are converted to 0–100 scores.

**Weights:**
- Interest fit: 35%
- Budget fit: 25%
- Weather fit: 15%
- Flight price: 15%
- Travel time: 10%

**Output:** destinations are ranked using a personalized multi-criteria decision score. The recommendation text explains both strengths and trade-offs.

**Next version:** connect live airfare, weather, attraction, and generative-AI APIs.
""")

st.caption("MBA AI project prototype. Airfare and destination values are demo data rather than live quotes.")
