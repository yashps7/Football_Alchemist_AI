import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key="")  # Leave empty for user input

def scrape_player_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Get the player's age, team, and position
    position = soup.select_one('p:-soup-contains("Position")').text.split(':')[-2].split(' ')[0].strip()
    birthday = soup.select_one('span[id="necro-birth"]').text.strip()
    age = (datetime.now() - datetime.strptime(birthday, '%B %d, %Y')).days // 365
    team = soup.select_one('p:-soup-contains("Club")').text.split(':')[-1].strip()

    return position, age, team

def get_scouting_report(player_name, position, age, team, df):
    prompt = f"""
    I need you to create a scouting report on {player_name}. Can you provide me with a summary of their strengths and weaknesses?

    Here is the data I have on him:

    Player: {player_name}
    Position: {position}
    Age: {age}
    Team: {team}

    {df.to_markdown()}

    Return the scouting report in the following markdown format:

    # Scouting Report for {player_name}

    ## Strengths
    < a list of 1 to 3 strengths >

    ## Weaknesses
    < a list of 1 to 3 weaknesses >

    ## Summary
    < a brief summary of the player's overall performance and if he would be beneficial to the team >
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional football (soccer) scout."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content

def main():
    st.title("Football Player Scouting Report Generator")

    player_name = st.text_input("Enter player name:")
    url = st.text_input("Enter player's FBref URL:")
    api_key = st.text_input("Enter your OpenAI API key:", type="password")  # New input for API key

    if st.button("Generate Scouting Report"):
        try:
            df = pd.read_html(url)[0]
            position, age, team = scrape_player_data(url)
            client.api_key = api_key  # Set the OpenAI API key from user input
            scouting_report = get_scouting_report(player_name, position, age, team, df)
            st.markdown(scouting_report)
        except Exception as e:
            st.error("Error occurred while generating scouting report. Please check the input URL or try again later.")


    # Text above the links
    st.write("For more you can click these links below:")
    
    # Add links to Shotmap and Heatmap at the bottom of the window
    st.markdown("[Shotmap](https://colab.research.google.com/drive/1OwivYEv4U1VO9HBe1E68sZz7Zkn_1eVZ)")
    st.markdown("[Heatmap](https://colab.research.google.com/drive/1QjzVLuMEm_ZH-jvc64-XSJn64yyHwF7o)")

if __name__ == "__main__":
    main()
