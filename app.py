import streamlit as st
import pandas as pd
import requests
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from openai import OpenAI
from urllib.parse import urlparse

st.set_page_config(layout="wide")

st.markdown('<h1 style="color: #F3FF02; font-family:Arial; font-size: 60px; text-align: center;">Football Alchemist AI</h1>', unsafe_allow_html=True)
st.markdown('<h3 style="color: #FF02FC; font-family:Arial; font-size: 20px; text-align: center;">Transforming raw football data into golden scouting reports through AI alchemy. </h3>', unsafe_allow_html=True)

st.caption("For player statistics, we initially used the FBref website to scrape all essential data such as name, age, etc. However, recently scraping data has become challenging, so we moved to Fotmob. Despite this, we still need to scrape statistics from the [FBref website](https://fbref.com/en/). Therefore before proceeding, we need to run [colab file](https://colab.research.google.com/drive/1nx0BSmhoenc8joP-EsYNtQQzx2_F9jwa) first to get the statistics data, which will automatically be stored in GitHub as long as the GitHub token is valid (currently for 30 days as of 18/05/2024")
st.sidebar.title("Enter Fotmob Player Profile URL to proceed and Draw Insights 🎨")
st.sidebar.caption("Go to [Fotmob](https://www.fotmob.com/) to search player ")
fotmob = st.sidebar.text_input("Enter the Fotmob player URL:")
# Check if the OpenAI API key is valid
if not 'players' in fotmob:
    st.sidebar.warning('Enter correct player link!', icon='⚠️')

st.sidebar.title("Enter your OpenAI API Key")
st.sidebar.caption("Go to [OpenAI](https://platform.openai.com/settings/profile?tab=api-keys) to get your own api ")
openkey = st.sidebar.text_input("Enter your OpenAI API key:", type="password")  # New input for API key

# Check if the OpenAI API key is valid
if not openkey.startswith('sk-'):
    st.sidebar.warning('Enter your and correct API key!', icon='⚠️')
else:
    # Initialize the OpenAI client with the valid API key
    client = OpenAI(api_key=openkey)
    
# Initialize OpenAI client
api_key = OpenAI(api_key=openkey)

# Function to extract player bio stats
def extract_player_bio(soup):
    player_info = {}

    # Extracting player's age
    bio_stats = soup.find_all('div', class_='css-1u6v53x-PlayerBioStatCSS e1478frm3')
    for stat in bio_stats:
        title = stat.find('div', class_='css-10h4hmz-StatTitleCSS e1478frm2').find('span').text.strip()
        value = stat.find('div', class_='css-to3w1c-StatValueCSS e1478frm1').find('span').text.strip() if stat.find('span') else None
        if "years" in value:
            player_info['Age'] = value

    # Extracting the player's team
    team_section = soup.find('div', class_='css-3ephfi-TeamCSS e1wpoh897')
    if team_section:
        player_info['Team'] = team_section.get_text(strip=True)

    # Extracting primary position
    primary_position = soup.find('div', class_='css-1g41csj-PositionsCSS e7shxg62')
    player_info['Primary Position'] = primary_position.text.strip() if primary_position else None

    # Extracting the player's league
    league_section = soup.find('h2', class_='css-1eyg8b0-HeaderText e8flwhe3')
    if league_section:
        player_info['League'] = league_section.get_text(strip=True)[:-9]     # -9 for removing league error
    
    # Extracting player's market value
    market_value = soup.find('div', class_='css-to3w1c-StatValueCSS', string=lambda string: string and '€' in string).text
    player_info['Market_Value'] = market_value
    
    return player_info

def printStats(table):
    data_table = table
    st.dataframe(data_table, width=1080, height=1300)

def get_scouting_report(player_name, position, age, team, league, value, table):
    # Fetching content from markdown file hosted on GitHub
    #markdown_url = url
    #markdown_content = requests.get(markdown_url).text
    #st.markdown(markdown_content, unsafe_allow_html=True)
    
    prompt = f"""
    I need you to create a scouting report on {player_name}. Can you provide me with a summary of their strengths and weaknesses?

    Here is the data I have on him:

    Player: {player_name}
    Position: {position}
    Age: {age}
    Team: {team}
    League: {league}
    Market Value: {value}
    
    {table}

    Return the scouting report in the following markdown format:

    # Scouting Report for {player_name}

    ## Player Overview
    < a general overview of a player >
    
    ## Key Performance Indicators
    < a list of 1 to 3 key performance indicators for that particular position in which player is playing >
    
    ## Strengths
    < a list of 1 to 5 strengths in few sentences each >

    ## Weaknesses
    < a list of 1 to 5 weaknesses in few sentences each >

    ## Area of Improvement
    < a list of 1 to 3 areas for improvement and potential strategies for development >
    
    ## Summary
    < a detailed summary of the player's overall performance and if he would be beneficial to the team with also market value aspect >
    """
    response = api_key.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional football (soccer) scout."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content

def radar_chart_from_url(url, name, league):
    # Send a GET request to the URL
    response = requests.get(url)

    # Parse the HTML content using BeautifulSoup
    traits = {}
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the div containing the traits
        traits_div = soup.find('div', class_='css-1l78068-PlayerTraitsContent e5ay90f4')

        if traits_div:
            # Find all spans containing trait labels and percentages
            trait_labels = traits_div.find_all('span', class_='css-1g16yy4-TraitText e5ay90f1')
            trait_percentages = traits_div.find_all('span', class_='css-wkdacm-TraitPercentage e5ay90f0')
            
            # Iterate over each pair of label and percentage
            for label, percentage in zip(trait_labels, trait_percentages):
                trait_name = label.text.strip()
                trait_percentage = percentage.text.strip()
                traits[trait_name] = trait_percentage

    categories = list(traits.keys())
    values = [float(val.strip('%')) for val in traits.values()]

    # Set the Seaborn style
    sns.set_style("darkgrid")

    # Create a radar chart with hexagonal fill
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    # Plot the outer hexagon
    ax.plot(np.linspace(0, 2*np.pi, len(categories)+1), np.ones(len(categories)+1)*100, color='black', linewidth=1)

    # Plot inner hexagons
    for percentage in range(10, 91, 10):
        inner_radius = percentage
        for i in range(len(categories)):
            angle = i / len(categories) * 2 * np.pi
            ax.plot([angle, (i + 1) / len(categories) * 2 * np.pi], [inner_radius, inner_radius], color='#D3D3D3', linestyle='dotted', linewidth=1)  # Very light black

    for i in range(len(categories)):
        angle = i / len(categories) * 2 * np.pi
        ax.plot([0, angle], [0, 100], color='#B6B6B6', linewidth=1)

    # Plot the radar chart with hexagonal fill
    for i in range(len(categories)):
        ax.fill([i / len(categories) * 2 * np.pi, (i + 1) / len(categories) * 2 * np.pi, (i + 1) / len(categories) * 2 * np.pi, i / len(categories) * 2 * np.pi],
                [0, 0, values[i], values[i]], color='#971e48', alpha=0.75)
        
    # Set the position of the trait labels above the hexagonal fill with percentages
    for i, (label, value) in enumerate(zip(categories, values)):
        angle = (i + 0.5) / len(categories) * 2 * np.pi
        if i in [0, 3]:
            ax.text(angle, 93, f"{label} ({int(value)}%)", ha='center', va='center', fontsize=12, fontweight='bold', color='#971e48', rotation=-60)
        elif i in [2, 5]:
            ax.text(angle, 93, f"{label} ({int(value)}%)", ha='center', va='center', fontsize=12, fontweight='bold', color='#971e48', rotation=60)
        else:
            ax.text(angle, 93, f"{label} ({int(value)}%)", ha='center', va='center', fontsize=12, fontweight='bold', color='#971e48')

    # Add a heading to the plot
    plt.title(f"{name} Traits Radar Chart in {league}", fontsize=12, fontweight='bold', color='#02FF9D', pad=20)
    
    ax.set_yticklabels([])
    ax.set_xticks(np.linspace(0, 2*np.pi, len(categories), endpoint=False))
    ax.set_xticklabels([])  # Remove default labels

    # Remove the background circle
    ax.set_frame_on(False)

    # Show the plot
    st.pyplot(fig)

def getPlayerData(soup, url):
    params = {}
    parsed_url = urlparse(url)
    params['playerId'] = parsed_url.path.split('/')[-2]
    
    league_year = soup.find('h2', class_='css-1eyg8b0-HeaderText').text
    season = league_year.split()[-1]
    
    link = soup.find('a', class_='css-16l5vhw-Header-applyMediumHover')
    uniqueNum = link.get('href').split('/')[-2]
    
    params['seasonId'] = season + '-' + uniqueNum
    
    response = requests.get('https://www.fotmob.com/api/playerStats', params=params)

    data = response.json()
    season = data['statsSection']['items']

    stats = list(season)
    flat_data = []
    for section in stats:
        for item in section['items']:
            flat_data.append({**item, 'section_title': section['title']})
    df = pd.DataFrame(flat_data)

    return df

# STREAMLIT APP
def main():
    # User input for URL
    url = fotmob

    if url:
        # Request the page content
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract and display player information
        player_info = extract_player_bio(soup)

        # Extracting Player Name
        name_section = soup.find('h1', class_='css-xgh3st-PlayerNameCSS e1wpoh898')
        if name_section:
            player_info['Player_Name'] = name_section.get_text(strip=True)
        
        st.sidebar.markdown("---")
        st.sidebar.markdown('<h1 style="color: #02FF9D;">Player Information</h1>', unsafe_allow_html=True)
        st.sidebar.write(f"**Name:** {player_info.get('Player_Name', 'N/A')}")
        st.sidebar.write(f"**Age:** {player_info.get('Age', 'N/A')}")
        st.sidebar.write(f"**Team:** {player_info.get('Team', 'N/A')}")
        st.sidebar.write(f"**Primary Position:** {player_info.get('Primary Position', 'N/A')}")
        st.sidebar.write(f"**League:** {player_info.get('League', 'N/A')}")
        
        st.sidebar.markdown("---")    
    
    st.sidebar.caption("For more similar projects :")
    st.sidebar.markdown("""
        <div style="display: flex; justify-content: space-between;">
            <a href="https://colab.research.google.com/drive/1OwivYEv4U1VO9HBe1E68sZz7Zkn_1eVZ">Shotmap</a>
            <a href="https://colab.research.google.com/drive/1QjzVLuMEm_ZH-jvc64-XSJn64yyHwF7o">Heatmap</a>
        </div>
    """, unsafe_allow_html=True)
    st.sidebar.caption("")
    st.sidebar.caption("My Accounts :")
    st.sidebar.markdown("""
        <div style="display: flex; justify-content: space-between;">
            <a href="https://github.com/yashps7">GitHub</a>
            <a href="https://www.linkedin.com/in/yash-sonone-095245218/">LinkedIn</a>
        </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")
        
    if st.button("Generate Scouting Report"):        
        df = pd.read_html(url)[0]
        position = player_info.get('Primary Position', 'N/A')
        age = player_info.get('Age', 'N/A')
        team = player_info.get('Team', 'N/A')
        league = player_info.get('League', 'N/A')
        dataTable = getPlayerData(soup, fotmob)
        scouting_report = get_scouting_report(player_info.get('Player_Name', 'N/A'), position, age, team, league, player_info.get('Market_Value', 'N/A'), dataTable)
        #st.markdown(scouting_report)
        #radar_chart_from_url(url, player_info.get('Player_Name', 'N/A'))
        
        # provide options to either view report, stat's or trait radar
        report, stats, radar = st.tabs(["Scouting Report", "Statistics", "Trait Radar"])
        with report:
            st.markdown(scouting_report)
        with stats:
            printStats(dataTable)
        with radar:
            radar_chart_from_url(url, player_info.get('Player_Name', 'N/A'), league)
        
if __name__ == "__main__":
    main()

