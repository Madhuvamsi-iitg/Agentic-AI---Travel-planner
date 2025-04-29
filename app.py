import streamlit as st
import json
import os
from serpapi import GoogleSearch
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini
from datetime import datetime
from types import SimpleNamespace
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# Set up Streamlit UI with a travel-friendly theme
st.set_page_config(page_title="🌍 AI Travel Planner", layout="wide")
st.markdown(
    """
    <style>
        .title {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: #ff5733;
        }
        .subtitle {
            text-align: center;
            font-size: 20px;
            color: #555;
        }
        .stSlider > div {
            background-color: #f9f9f9;
            padding: 10px;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title and subtitle
st.markdown('<h1 class="title">✈️ AI-Powered Travel Planner</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Plan your dream trip with AI! Get personalized recommendations for flights, hotels, and activities.</p>', unsafe_allow_html=True)

# User Inputs Section
st.markdown("### 🌍 Where are you headed?")
source = st.text_input("🛫 Departure City (IATA Code):", "BOM")  # Example: BOM for Mumbai
destination = st.text_input("🛬 Destination (IATA Code):", "DEL")  # Example: DEL for Delhi

st.markdown("### 📅 Plan Your Adventure")
num_days = st.slider("🕒 Trip Duration (days):", 1, 14, 5)
travel_theme = st.selectbox(
    "🎭 Select Your Travel Theme:",
    ["💑 Couple Getaway", "👨‍👩‍👧‍👦 Family Vacation", "🏔️ Adventure Trip", "🧳 Solo Exploration"]
)

# Divider for aesthetics
st.markdown("---")

st.markdown(
    f"""
    <div style="
        text-align: center; 
        padding: 15px; 
        background-color: #ffecd1; 
        border-radius: 10px; 
        margin-top: 20px;
    ">
        <h3>🌟 Your {travel_theme} to {destination} is about to begin! 🌟</h3>
        <p>Let's find the best flights, stays, and experiences for your unforgettable journey.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

def format_datetime(iso_string):
    try:
        dt = datetime.strptime(iso_string, "%Y-%m-%d %H:%M")
        return dt.strftime("%b-%d, %Y | %I:%M %p")  # Example: Mar-06, 2025 | 6:20 PM
    except:
        return "N/A"

activity_preferences = st.text_area(
    "🌍 What activities do you enjoy? (e.g., relaxing on the beach, exploring historical sites, nightlife, adventure)",
    "Relaxing on the beach, exploring historical sites"
)

departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")

# Sidebar Setup
st.sidebar.title("🌎 Travel Assistant")
st.sidebar.subheader("Personalize Your Trip")

# Travel Preferences
budget = st.sidebar.radio("💰 Budget Preference:", ["Economy", "Standard", "Luxury"])
flight_class = st.sidebar.radio("✈️ Flight Class:", ["Economy", "Business", "First Class"])
hotel_rating = st.sidebar.selectbox("🏨 Preferred Hotel Rating:", ["Any", "3⭐", "4⭐", "5⭐"])

# Packing Checklist
st.sidebar.subheader("🎒 Packing Checklist")
packing_list = {
    "👕 Clothes": True,
    "🩴 Comfortable Footwear": True,
    "🕶️ Sunglasses & Sunscreen": False,
    "📖 Travel Guidebook": False,
    "💊 Medications & First-Aid": True
}
for item, checked in packing_list.items():
    st.sidebar.checkbox(item, value=checked)

# Travel Essentials
st.sidebar.subheader("🛂 Travel Essentials")
visa_required = st.sidebar.checkbox("🛃 Check Visa Requirements")
travel_insurance = st.sidebar.checkbox("🛡️ Get Travel Insurance")
currency_converter = st.sidebar.checkbox("💱 Currency Exchange Rates")


os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["SERPAPI_API_KEY"] = os.getenv("SERPAPI_API_KEY")


params = {
        "engine": "google_flights",
        "departure_id": source,
        "arrival_id": destination,
        "outbound_date": str(departure_date),
        "return_date": str(return_date),
        "currency": "INR",
        "hl": "en",
        "api_key": os.getenv("SERPAPI_API_KEY")
    }

# Update your flight-related functions like this:

def fetch_flights(source, destination, departure_date, return_date):
    try:
        params = {
            "engine": "google_flights",
            "departure_id": source.upper(),  # Ensure uppercase IATA code
            "arrival_id": destination.upper(),
            "outbound_date": departure_date.strftime("%Y-%m-%d"),
            "return_date": return_date.strftime("%Y-%m-%d"),
            "currency": "INR",
            "hl": "en",
            "api_key": os.getenv("SERPAPI_API_KEY")
        }
        
        st.write("🔍 Searching for flights...")  # User feedback
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if not results or "best_flights" not in results:
            st.warning("No flight data available from API response")
            return {"best_flights": []}  # Return empty dict with expected structure
            
        return results
        
    except Exception as e:
        st.error(f"🚨 Error fetching flights: {str(e)}")
        return {"best_flights": []}  # Return empty dict with expected structure

def extract_cheapest_flights(flight_data):
    try:
        # Ensure we have valid flight data structure
        if not flight_data or not isinstance(flight_data, dict):
            return []
            
        best_flights = flight_data.get("best_flights", [])
        
        # Sort by price, handling missing prices by putting them last
        sorted_flights = sorted(
            best_flights,
            key=lambda x: float(x.get("price", float("inf")))
        )[:3]
        
        return sorted_flights
        
    except Exception as e:
        st.error(f"Error processing flight data: {str(e)}")
        return []
# AI Agents
researcher = Agent(
    name="Researcher",
    instructions=[
        "Identify the travel destination specified by the user.",
        "Gather detailed information on the destination, including climate, culture, and safety tips.",
        "Find popular attractions, landmarks, and must-visit places.",
        "Search for activities that match the users interests and travel style.",
        "Prioritize information from reliable sources and official travel guides.",
        "Provide well-structured summaries with key insights and recommendations."
    ],
    model=Gemini(id="gemini-2.5-flash-preview-04-17"),
    
    tools=[SerpApiTools(api_key=os.getenv("SERPAPI_API_KEY"))],
    add_datetime_to_instructions=True,
)


planner = Agent(
    name="Planner",
    instructions=[
        "Gather details about the user's travel preferences and budget.",
        "Create a detailed itinerary with scheduled activities and estimated costs.",
        "Ensure the itinerary includes transportation options and travel time estimates.",
        "Optimize the schedule for convenience and enjoyment.",
        "Present the itinerary in a structured format."
    ],
    model=Gemini(id="gemini-2.5-flash-preview-04-17"),
    add_datetime_to_instructions=True,
)

hotel_restaurant_finder = Agent(
    name="Hotel & Restaurant Finder",
    instructions=[
        f"Find 3-5 excellent {hotel_rating} hotels in {destination} suitable for {travel_theme}",
        f"Find 3-5 highly-rated restaurants in {destination} matching these preferences: {activity_preferences}",
        "For each hotel and restaurant, include: name, address, price range, rating, and brief description",
        "Format the results clearly with headings for Hotels and Restaurants sections",
        "If no results found, suggest alternative search terms"
    ],
    model=Gemini(id="gemini-2.5-flash-preview-04-17"),
    tools=[SerpApiTools(api_key=os.getenv("SERPAPI_API_KEY"))],
    add_datetime_to_instructions=True,
)
if st.button("🚀 Generate Travel Plan"):
    # 1) FETCH FLIGHTS
    with st.spinner("✈️ Fetching best flight options..."):
        flight_data = fetch_flights(source, destination, departure_date, return_date)
        cheapest_flights = extract_cheapest_flights(flight_data)
        if not cheapest_flights:
            st.warning("⚠️ No flights returned. Check your SERPAPI_API_KEY, departure/arrival codes, or try again later.")
            # (Optional) log raw response for debugging
            st.text(f"Raw flight response: {flight_data}")

    # 2) RESEARCH ATTRACTIONS
    # Initialize a dummy result so research_results.content always exists
    research_results = SimpleNamespace(content="")
    with st.spinner("🔍 Researching best attractions & activities..."):
        try:
            research_prompt = (
                f"Research the best attractions and activities in {destination} "
                f"for a {num_days}-day {travel_theme.lower()} trip. "
                f"The traveler enjoys: {activity_preferences}. Budget: {budget}. "
                f"Flight Class: {flight_class}. Hotel Rating: {hotel_rating}. "
                f"Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}."
            )
            research_results = researcher.run(research_prompt, stream=False)
            if not research_results.content:
                st.warning("No research content returned; the agent may not have found anything.")
        except Exception as e:
            st.error(f"Research failed: {e}")
            # research_results.content remains "", so planner won’t crash

    # 3) HOTELS & RESTAURANTS
    with st.spinner("🏨 Searching for hotels & restaurants..."):
        hotel_restaurant_prompt = (
            f"Find the best hotels and restaurants near popular attractions in {destination} "
            f"for a {travel_theme.lower()} trip. Budget: {budget}. Hotel Rating: {hotel_rating}. "
            f"Preferred activities: {activity_preferences}."
        )
        hotel_restaurant_results = hotel_restaurant_finder.run(hotel_restaurant_prompt, stream=False)

    # 4) BUILD ITINERARY
    with st.spinner("🗺️ Creating your personalized itinerary..."):
        try:
            planning_prompt = (
                f"Based on the following data, create a {num_days}-day itinerary for a "
                f"{travel_theme.lower()} trip to {destination}. "
                f"The traveler enjoys: {activity_preferences}. Budget: {budget}. "
                f"Flight Class: {flight_class}. Hotel Rating: {hotel_rating}. "
                f"Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}. "
                f"Research: {research_results.content}. "
                f"Flights: {json.dumps(cheapest_flights)}. "
                f"Hotels & Restaurants: {hotel_restaurant_results.content}."
            )
            itinerary = planner.run(planning_prompt, stream=False)
        except Exception as e:
            st.error(f"Failed to build itinerary: {e}")
            itinerary = SimpleNamespace(content="")
    # Display Results
    st.subheader("✈️ Cheapest Flight Options")
    if cheapest_flights:
        cols = st.columns(len(cheapest_flights))
        for idx, flight in enumerate(cheapest_flights):
            with cols[idx]:
                airline_logo = flight.get("airline_logo", "")
                airline_name = flight.get("airline", "Unknown Airline")
                price = flight.get("price", "Not Available")
                total_duration = flight.get("total_duration", "N/A")
                
                flights_info = flight.get("flights", [{}])
                departure = flights_info[0].get("departure_airport", {})
                arrival = flights_info[-1].get("arrival_airport", {})
                airline_name = flights_info[0].get("airline", "Unknown Airline") 
                
                departure_time = format_datetime(departure.get("time", "N/A"))
                arrival_time = format_datetime(arrival.get("time", "N/A"))
                
                departure_token = flight.get("departure_token", "")

                if departure_token:
                    params_with_token = {
                        **params,
                        "departure_token": departure_token  # Add the token here
                    }
                    search_with_token = GoogleSearch(params_with_token)
                    results_with_booking = search_with_token.get_dict()

                    booking_options = results_with_booking['best_flights'][idx]['booking_token']

                booking_link = f"https://www.google.com/travel/flights?tfs="+booking_options if booking_options else "#"
                print(booking_link)
                # Flight card layout
                st.markdown(
                    f"""
                    <div style="
                        border: 2px solid #ddd; 
                        border-radius: 10px; 
                        padding: 15px; 
                        text-align: center;
                        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
                        background-color: #f9f9f9;
                        margin-bottom: 20px;
                    ">
                        <img src="{airline_logo}" width="100" alt="Flight Logo" />
                        <h3 style="margin: 10px 0;">{airline_name}</h3>
                        <p><strong>Departure:</strong> {departure_time}</p>
                        <p><strong>Arrival:</strong> {arrival_time}</p>
                        <p><strong>Duration:</strong> {total_duration} min</p>
                        <h2 style="color: #008000;">💰 {price}</h2>
                        <a href="{booking_link}" target="_blank" style="
                            display: inline-block;
                            padding: 10px 20px;
                            font-size: 16px;
                            font-weight: bold;
                            color: #fff;
                            background-color: #007bff;
                            text-decoration: none;
                            border-radius: 5px;
                            margin-top: 10px;
                        ">🔗 Book Now</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("⚠️ No flight data available.")

    st.subheader("🏨 Hotels & Restaurants")
    st.write(hotel_restaurant_results.content)

    st.subheader("🗺️ Your Personalized Itinerary")
    st.write(itinerary.content)

    st.success("✅ Travel plan generated successfully!")