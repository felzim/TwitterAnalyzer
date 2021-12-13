import sys
from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit import cli as stcli
import matplotlib.pyplot as plt
import seaborn as sns

# Installation von snscrape (development version):
# pip install git+https://github.com/JustAnotherArchivist/snscrape.git
import snscrape.modules.twitter as sntwitter



####################### Twitter Frequency App
########## Autor: Felix Zimmermann
#
#    Prototyp einer Applikation zur Analyse von Twitterdaten. Nach Eingabe eines oder mehrerer
#    Begriffe wird für einen gewählten Zeitraum die Anzahl der Tweets, die diese(n) Begriff(e)
#    enthalten, grafisch in einem Barplot ausgegeben. Es kann ausgewählt werden, ob der
#    Barplots mit einer monatlichen, täglichen oder auch jährlichen Frequenz ausgegeben wird.
#    Zusätzlich kann eine CSV-Datei mit den entsprechenden Twitterdaten für weitere Analysen
#    heruntergeladen werden.
#
#    TODO: Readme


class TwitterAnalysis():

    def __init__(self):

        # Streamlit-Elemente verstecken
        hide_streamlit_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    </style>
                    """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)


    def getData(term, date_since, date_until):
        '''
        Funktion, die mit snscrape für einen gegebenen Zeitraum Twitterdaten sammelt,
        diese in einem Dataframe speichert und zurück gibt.
        '''

        tweets_list = []
        while True:
            try:
                for i, tweet in enumerate(sntwitter.TwitterSearchScraper(f'{term} since:{date_since} until:{date_until}').get_items()):
                    tweets_list.append([tweet.date, tweet.id, tweet.content, tweet.user.username, tweet.hashtags])
                break
            except:
                continue

        tweets_df = pd.DataFrame(tweets_list, columns=['Datetime', 'Tweet Id', 'Text', 'Username', 'Hashtags'])
        return tweets_df


    def process_df(tweets_df, date_since, date_until):
        '''
        Funktion, die die mit getData() gesammelten Twitterdaten weiter verarbeitet. Hinzugefügt wird
        eine Zeitreihe und eine Gruppierung nach Tagen, Monaten und Jahren.
        '''

        tweets_df['Datetime'] = pd.to_datetime(tweets_df['Datetime'])
        tweets_df['Year_Month'] = tweets_df['Datetime'].dt.strftime('%Y-%m')
        tweets_df = tweets_df.sort_values(by='Datetime')

        tweets_df['Date'] = tweets_df['Datetime'].dt.strftime('%Y-%m-%d')
        tweets_df['Date'] = pd.to_datetime(tweets_df['Date'])

        # Zeitreihe erstellen
        daterange = pd.date_range(start=date_since.strftime('%Y-%m-%d'), end=date_until.strftime('%Y-%m-%d'), freq='d')
        dr_df = pd.DataFrame(daterange)
        dr_df.columns = ['Date']

        tweets_df = pd.merge(dr_df, tweets_df, how='left', on='Date')


        # Tweets nach Tagen
        count_days = tweets_df.groupby('Date').count()['Tweet Id']
        count_days_df = pd.DataFrame(count_days)
        count_days_df.columns = ['count_days']

        tweets_df = pd.merge(tweets_df, count_days_df, on='Date')

        # Tweets nach Monaten
        tweets_df['Year_Month'] = tweets_df['Date'].dt.strftime('%Y-%m')

        count_months = tweets_df.groupby('Year_Month').count()['Tweet Id']
        count_months_df = pd.DataFrame(count_months)
        count_months_df.columns = ['count_months']

        tweets_df = pd.merge(tweets_df, count_months_df, on='Year_Month')

        # Tweets nach Jahren
        tweets_df['Year'] = tweets_df['Date'].dt.strftime('%Y')

        count_years = tweets_df.groupby('Year').count()['Tweet Id']
        count_years_df = pd.DataFrame(count_years)
        count_years_df.columns = ['count_years']

        tweets_df = pd.merge(tweets_df, count_years_df, on='Year')

        return tweets_df


    # Streamlit-Oberfläche
    st.title('Twitter Term Frequency')
    term = st.text_input(label = 'Begriffe', value = 'Soziale Republik')

    today = datetime.today().strftime('%Y-%m-%d')
    date_since = st.date_input(label = 'Beginn Zeitraum', value = datetime.strptime('2021-01-01', '%Y-%m-%d'))
    date_until = st.date_input(label = 'Ende Zeitraum', value = datetime.strptime(today, '%Y-%m-%d'))

    frequency = st.radio(
        label = "Frequenz:",
        options = ('Monate', 'Jahre', 'Tage'),
        index = 0)

    # Twitter-Scraper starten
    tweets_df = getData(term, date_since, date_until)

    # Export der Rohdaten für CSV-Datei
    tweets_df_export = tweets_df.copy()

    # Daten verarbeiten
    tweets_df = process_df(tweets_df, date_since, date_until)

    # Grafik ausgeben
    fig = plt.figure(figsize=(10, 4))
    fig, ax = plt.subplots()

    if frequency == 'Monate':
        g = sns.barplot(x = tweets_df['Year_Month'], y = tweets_df['count_months'])
    elif frequency == 'Tage':
        g = sns.barplot(x=tweets_df['Date'].dt.strftime('%Y-%m-%d'), y=tweets_df['count_days'])
    elif frequency == 'Jahre':
        g = sns.barplot(x=tweets_df['Year'], y=tweets_df['count_years'])

    ax.set_xticklabels(g.get_xticklabels(), rotation=90)
    ax.set(xlabel=frequency, ylabel='Nennungen')
    plt.title(f'Begriffe: {term}; Zeitraum: {date_since} bis {date_until}')
    plt.tight_layout()

    st.pyplot(fig)

    # Dataframe ausgeben
    st.subheader('Dataframe')
    st.write(tweets_df_export)

    csv = tweets_df_export.to_csv()

    st.download_button(
        label="Dataframe als csv speichern",
        data=csv,
        file_name='tweets_df.csv',
        mime='text/csv',
    )


if __name__ == '__main__':

    if st._is_running_with_streamlit:
        TwitterAnalysis()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())