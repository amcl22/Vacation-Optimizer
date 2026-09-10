import pandas as pd
import streamlit as st
from datetime import date

st.set_page_config(
    page_title="AI Vacation Destination Optimizer",
    page_icon="✈️",
    layout="wide"
)

# ----------------------------------------------------
# PAGE STYLING
# ----------------------------------------------------

st.markdown("""
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


# ----------------------------------------------------
# LOAD DESTINATION DATA
# ----------------------------------------------------

@st.cache_data
def load_data():
    return pd.read_csv("data/destinations.csv")


df = load_data()


# ----------------------------------------------------
# U.S. AIRPORT OPTIONS
# ----------------------------------------------------

airports = {
    "PHL — Philadelphia International": {
        "fare_factor": 1.00,
        "time_adjustment": 0.0
    },

    "JFK — New York John F. Kennedy": {
        "fare_factor": 0.95,
        "time_adjustment": -0.3
    },

    "EWR — Newark Liberty International": {
        "fare_factor": 0.96,
        "time_adjustment": -0.2
    },

    "BOS — Boston Logan International": {
        "fare_factor": 0.97,
        "time_adjustment": -0.3
    },

    "IAD — Washington Dulles International": {
        "fare_factor": 0.98,
        "time_adjustment": 0.0
    },

    "BWI — Baltimore/Washington International": {
        "fare_factor": 1.00,
        "time_adjustment": 0.2
    },

    "ATL — Hartsfield-Jackson Atlanta International": {
        "fare_factor": 0.94,
        "time_adjustment": 0.4
    },

    "MIA — Miami International": {
        "fare_factor": 0.95,
        "time_adjustment": 0.6
    },

    "FLL — Fort Lauderdale-Hollywood International": {
        "fare_factor": 0.98,
        "time_adjustment": 0.7
    },

    "MCO — Orlando International": {
        "fare_factor": 0.98,
        "time_adjustment": 0.7
    },

    "CLT — Charlotte Douglas International": {
        "fare_factor": 0.98,
        "time_adjustment": 0.3
    },

    "DTW — Detroit Metropolitan Wayne County": {
        "fare_factor": 1.00,
        "time_adjustment": 0.3
    },

    "ORD — Chicago O'Hare International": {
        "fare_factor": 0.94,
        "time_adjustment": 0.4
    },

    "MSP — Minneapolis-Saint Paul International": {
        "fare_factor": 0.98,
        "time_adjustment": 0.8
    },

    "DFW — Dallas/Fort Worth International": {
        "fare_factor": 0.95,
        "time_adjustment": 1.0
    },

    "IAH — Houston George Bush Intercontinental": {
        "fare_factor": 0.96,
        "time_adjustment": 1.1
    },

    "AUS — Austin-Bergstrom International": {
        "fare_factor": 1.00,
        "time_adjustment": 1.2
    },

    "DEN — Denver International": {
        "fare_factor": 0.96,
        "time_adjustment": 1.3
    },

    "SLC — Salt Lake City International": {
        "fare_factor": 1.00,
        "time_adjustment": 1.7
    },

    "PHX — Phoenix Sky Harbor International": {
        "fare_factor": 0.98,
        "time_adjustment": 2.0
    },

    "LAS — Harry Reid International": {
        "fare_factor": 0.97,
        "time_adjustment": 2.0
    },

    "LAX — Los Angeles International": {
        "fare_factor": 0.92,
        "time_adjustment": 2.5
    },

    "SFO — San Francisco International": {
        "fare_factor": 0.93,
        "time_adjustment": 2.4
    },

    "SEA — Seattle-Tacoma International": {
        "fare_factor": 0.95,
        "time_adjustment": 2.7
    },

    "SAN — San Diego International": {
        "fare_factor": 0.98,
        "time_adjustment": 2.6
    },

    "PDX — Portland International": {
        "fare_factor": 1.00,
        "time_adjustment": 2.8
    },

    "HNL — Daniel K. Inouye International": {
        "fare_factor": 1.18,
        "time_adjustment": 5.5
    }
}


# ----------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------

def inverse_score(value, low, high):

    if high == low:
        return 100.0

    return max(
        0.0,
        min(
            100.0,
            100 * (high - value) / (high - low)
        )
    )


def weather_score(
    avg_temp_f,
    rain_days,
    preferred_low,
    preferred_high
):

    if preferred_low <= avg_temp_f <= preferred_high:
        temp = 100

    else:

        d = min(
            abs(avg_temp_f - preferred_low),
            abs(avg_temp_f - preferred_high)
        )

        temp = max(
            0,
            100 - 7 * d
        )

    rain = max(
        0,
        100 - 8 * rain_days
    )

    return (
        0.75 * temp
        + 0.25 * rain
    )


def budget_score(cost, budget):

    if cost <= budget:

        return min(
            100,
            85 + (1 - cost / budget) * 30
        )

    over = (
        cost - budget
    ) / budget

    return max(
        0,
        80 - over * 180
    )


def interest_score(row, weights):

    vals = {

        "Nature": row["nature_score"],

        "Food": row["food_score"],

        "History": row["history_score"],

        "Nightlife": row["nightlife_score"],

        "Beach": row["beach_score"],
    }

    total = (
        sum(weights.values())
        or 1
    )

    return sum(
        vals[k] * weights[k]
        for k in vals
    ) / total


def explanation(
    row,
    budget,
    max_flight,
    weights,
    airport_code
):

    strengths = []

    for label, col in [

        ("nature and scenery", "nature_score"),

        ("food", "food_score"),

        ("history and culture", "history_score"),

        ("nightlife", "nightlife_score"),

        ("beaches", "beach_score"),
    ]:

        if row[col] >= 85:
            strengths.append(label)

    reasons = (
        ", ".join(strengths[:3])
        if strengths
        else "its overall balance"
    )

    tradeoffs = []

    if row["estimated_trip_cost"] > budget:

        tradeoffs.append(
            "the estimated trip cost is above your budget"
        )

    if row["adjusted_flight_hours"] > max_flight:

        tradeoffs.append(
            "the travel time exceeds your preferred maximum"
        )

    if row["rain_days"] >= 4:

        tradeoffs.append(
            "the season can be relatively rainy"
        )

    if (
        row["beach_score"] < 50
        and weights["Beach"] >= 7
    ):

        tradeoffs.append(
            "it is not a particularly strong beach destination"
        )

    if (
        row["nightlife_score"] < 50
        and weights["Nightlife"] >= 7
    ):

        tradeoffs.append(
            "the nightlife is weaker than you prefer"
        )

    tradeoff = (
        tradeoffs[0]
        if tradeoffs
        else "there are no major mismatches with your current preferences"
    )

    return (

        f"{row['city']} performs well because of {reasons}. "

        f"The estimated total trip cost is about "
        f"${row['estimated_trip_cost']:,.0f}, "

        f"with estimated round-trip airfare of "
        f"${row['adjusted_flight_cost']:,.0f} "

        f"from {airport_code}. "

        f"Estimated travel time is about "
        f"{row['adjusted_flight_hours']:.1f} hours. "

        f"The main trade-off is that {tradeoff}."
    )


# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------

st.sidebar.title(
    "Plan Your Trip ✈️"
)

st.sidebar.caption(
    "Tell us what your ideal vacation looks like."
)


selected_airport = st.sidebar.selectbox(

    "Departure airport",

    list(airports.keys())
)


airport_code = selected_airport.split(" — ")[0]

airport_settings = airports[selected_airport]


start_date = st.sidebar.date_input(

    "Departure date",

    date(2027, 6, 13)
)


end_date = st.sidebar.date_input(

    "Return date",

    date(2027, 6, 20)
)


budget = st.sidebar.slider(

    "Total trip budget",

    1000,

    7000,

    2500,

    100
)


max_flight = st.sidebar.slider(

    "Preferred maximum travel time (hours)",

    4,

    20,

    10
)


preferred_low = st.sidebar.slider(

    "Preferred daytime temp — low °F",

    45,

    80,

    65
)


preferred_high = st.sidebar.slider(

    "Preferred daytime temp — high °F",

    60,

    95,

    80
)


st.sidebar.markdown(
    "### What matters most?"
)


weights = {

    "Nature": st.sidebar.slider(
        "Nature / scenery",
        0,
        10,
        10
    ),

    "Food": st.sidebar.slider(
        "Food",
        0,
        10,
        8
    ),

    "History": st.sidebar.slider(
        "History / culture",
        0,
        10,
        7
    ),

    "Nightlife": st.sidebar.slider(
        "Nightlife",
        0,
        10,
        3
    ),

    "Beach": st.sidebar.slider(
        "Beach",
        0,
        10,
        2
    ),
}


# ----------------------------------------------------
# CALCULATE TRIP LENGTH
# ----------------------------------------------------

nights = max(
    1,
    (end_date - start_date).days
)


# ----------------------------------------------------
# CREATE SCORED DATAFRAME
# ----------------------------------------------------

scored = df.copy()


# ----------------------------------------------------
# ADJUST AIRFARE BASED ON ORIGIN
# ----------------------------------------------------

scored["adjusted_flight_cost"] = (

    scored["sample_roundtrip_flight"]
    * airport_settings["fare_factor"]

).round(0)


scored["adjusted_flight_hours"] = (

    scored["flight_hours"]
    + airport_settings["time_adjustment"]

).clip(lower=1)


# ----------------------------------------------------
# ESTIMATED TOTAL TRIP COST
# ----------------------------------------------------

scored["estimated_trip_cost"] = (

    scored["adjusted_flight_cost"]

    + nights * scored["hotel_per_night"]

    + (nights + 1) * scored["daily_food"]

    + (nights + 1) * scored["daily_transit"]

    + (nights + 1) * scored["daily_activities"]
)


# ----------------------------------------------------
# NORMALIZATION
# ----------------------------------------------------

fmin = scored[
    "adjusted_flight_cost"
].min()

fmax = scored[
    "adjusted_flight_cost"
].max()


tmin = scored[
    "adjusted_flight_hours"
].min()

tmax = scored[
    "adjusted_flight_hours"
].max()


scored["flight_cost_score"] = (

    scored[
        "adjusted_flight_cost"
    ].apply(

        lambda x:

        inverse_score(
            x,
            fmin,
            fmax
        )
    )
)


scored["flight_time_score"] = (

    scored[
        "adjusted_flight_hours"
    ].apply(

        lambda x:

        inverse_score(
            x,
            tmin,
            tmax
        )
    )
)


scored["weather_match_score"] = (

    scored.apply(

        lambda r:

        weather_score(

            r["avg_temp_f"],

            r["rain_days"],

            preferred_low,

            preferred_high
        ),

        axis=1
    )
)


scored["budget_match_score"] = (

    scored[
        "estimated_trip_cost"
    ].apply(

        lambda x:

        budget_score(
            x,
            budget
        )
    )
)


scored["interest_match_score"] = (

    scored.apply(

        lambda r:

        interest_score(
            r,
            weights
        ),

        axis=1
    )
)


# ----------------------------------------------------
# FINAL DESTINATION SCORE
# ----------------------------------------------------

scored["overall_score"] = (

    0.35
    * scored["interest_match_score"]

    + 0.25
    * scored["budget_match_score"]

    + 0.15
    * scored["weather_match_score"]

    + 0.15
    * scored["flight_cost_score"]

    + 0.10
    * scored["flight_time_score"]
)


# PENALTY FOR EXCEEDING PREFERRED FLIGHT TIME

scored.loc[

    scored[
        "adjusted_flight_hours"
    ] > max_flight,

    "overall_score"

] -= (

    scored[
        "adjusted_flight_hours"
    ]

    - max_flight

) * 2.5


scored["overall_score"] = (

    scored[
        "overall_score"
    ]

    .clip(
        0,
        100
    )

    .round(1)
)


scored = (

    scored

    .sort_values(
        "overall_score",
        ascending=False
    )

    .reset_index(
        drop=True
    )
)


# ----------------------------------------------------
# MAIN PAGE
# ----------------------------------------------------

st.title(
    "Where Should You Go Next? ✈️"
)


st.markdown(

    "Personalized destination recommendations based on your "

    "budget, travel style, weather preferences, and interests."
)


st.container(border=True).markdown("""
### 🌎 Find your perfect getaway

Compare destinations using **cost, weather, travel time, and what actually matters to you.**
""")


# ----------------------------------------------------
# SUMMARY
# ----------------------------------------------------

c1, c2, c3, c4 = st.columns(4)


c1.metric(
    "Trip length",
    f"{nights} nights"
)


c2.metric(
    "Budget",
    f"${budget:,}"
)


c3.metric(
    "Flying from",
    airport_code
)


c4.metric(
    "Top match",
    f"{scored.iloc[0]['overall_score']:.1f}%"
)


st.divider()


# ----------------------------------------------------
# TOP DESTINATION
# ----------------------------------------------------

top = scored.iloc[0]


st.subheader(
    f"Your Best Match: "
    f"{top['city']}, "
    f"{top['country']} 🌍"
)


a, b, c, d = st.columns(4)


a.metric(
    "Match score",
    f"{top['overall_score']:.1f}%"
)


b.metric(
    "Est. trip cost",
    f"${top['estimated_trip_cost']:,.0f}"
)


c.metric(
    f"Est. airfare from {airport_code}",
    f"${top['adjusted_flight_cost']:,.0f}"
)


d.metric(
    "Travel time",
    f"{top['adjusted_flight_hours']:.1f} hrs"
)


st.info(

    explanation(

        top,

        budget,

        max_flight,

        weights,

        airport_code
    )
)


# ----------------------------------------------------
# TOP DESTINATIONS
# ----------------------------------------------------

st.markdown(
    "### Other Destinations You'll Love"
)


table = scored.head(5)[

    [
        "city",

        "country",

        "overall_score",

        "estimated_trip_cost",

        "adjusted_flight_cost",

        "avg_temp_f",

        "adjusted_flight_hours",

        "interest_match_score"
    ]

].copy()


table.columns = [

    "Destination",

    "Country",

    "Match %",

    "Est. Trip Cost",

    "Est. Airfare",

    "Avg Temp °F",

    "Travel Hours",

    "Interest Fit"
]


table[
    "Est. Trip Cost"
] = (

    table[
        "Est. Trip Cost"
    ].map(

        lambda x:

        f"${x:,.0f}"
    )
)


table[
    "Est. Airfare"
] = (

    table[
        "Est. Airfare"
    ].map(

        lambda x:

        f"${x:,.0f}"
    )
)


table[
    "Interest Fit"
] = (

    table[
        "Interest Fit"
    ]

    .round(1)
)


st.dataframe(

    table,

    hide_index=True,

    use_container_width=True
)


# ----------------------------------------------------
# CHART
# ----------------------------------------------------

st.markdown(
    "### Top 10 Destination Ranking"
)


st.bar_chart(

    scored

    .head(10)

    .set_index("city")[

        ["overall_score"]

    ]
)


# ----------------------------------------------------
# EXPLORE A DESTINATION
# ----------------------------------------------------

st.markdown(
    "### Explore a Destination"
)


selected = st.selectbox(

    "Choose a destination",

    scored["city"].tolist()
)


sel = scored[

    scored["city"]
    == selected

].iloc[0]


m1, m2, m3, m4, m5 = st.columns(5)


m1.metric(
    "Budget fit",
    f"{sel['budget_match_score']:.0f}"
)


m2.metric(
    "Weather fit",
    f"{sel['weather_match_score']:.0f}"
)


m3.metric(
    "Interest fit",
    f"{sel['interest_match_score']:.0f}"
)


m4.metric(
    "Flight-price fit",
    f"{sel['flight_cost_score']:.0f}"
)


m5.metric(
    "Travel-time fit",
    f"{sel['flight_time_score']:.0f}"
)


st.write(

    explanation(

        sel,

        budget,

        max_flight,

        weights,

        airport_code
    )
)


# ----------------------------------------------------
# DESTINATION PROFILE
# ----------------------------------------------------

with st.expander(
    "Destination interest profile"
):

    profile = pd.DataFrame({

        "Category": [

            "Nature",

            "Food",

            "History",

            "Nightlife",

            "Beach"
        ],

        "Destination Score": [

            sel["nature_score"],

            sel["food_score"],

            sel["history_score"],

            sel["nightlife_score"],

            sel["beach_score"]
        ]
    })


    st.dataframe(

        profile,

        hide_index=True,

        use_container_width=True
    )


# ----------------------------------------------------
# MODEL EXPLANATION
# ----------------------------------------------------

with st.expander(
    "How the model works"
):

    st.markdown("""

**Inputs**

The traveler selects:

- Departure airport
- Trip dates
- Budget
- Maximum preferred travel time
- Preferred weather
- Nature preference
- Food preference
- History/culture preference
- Nightlife preference
- Beach preference


**Normalization**

Airfare, travel time, budget fit,
weather, and destination characteristics
are converted into comparable 0–100 scores.


**Model weights**

- Interest fit: 35%
- Budget fit: 25%
- Weather fit: 15%
- Flight price: 15%
- Travel time: 10%


**Airport adjustment**

The prototype adjusts airfare and travel-time
estimates based on the selected U.S. origin airport.

This simulates differences between departure markets
until live airfare APIs are connected.


**Output**

Destinations are ranked using a personalized
multi-criteria decision score.

The recommendation then explains both the
destination's strengths and its major trade-offs.


**Future version**

The model can connect to:

- Live airfare data
- Historical and forecast weather
- Hotel pricing
- Attraction information
- Generative AI recommendations

""")


st.caption(

    "MBA AI project prototype. "

    "Airfare and destination values currently use modeled estimates "

    "rather than live booking quotes."
)
