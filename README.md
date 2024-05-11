# YOUTUBE-DATA-HARVESTING-PROJECT---CAPSTONE
YOUTUBE DATA HARVESTING PROJECT - CAPSTONE1
Project Title: YouTube Data Harvesting and Warehousing

Description:
The YouTube Data Harvesting and Warehousing project is designed to extract, transform, and warehouse data from YouTube channels using the YouTube Data API. This project allows users to extract data such as channel details, playlist information, video details, and comments from YouTube channels, transform it into a structured format, and store it in a MySQL database for further analysis and visualization.

Features:

Extraction: Users can input a YouTube channel ID, and the application extracts channel details such as name, description, subscribers count, total views, total videos, etc., using the YouTube Data API.
Transformation: The extracted data is then transformed into a structured format suitable for storage in a MySQL database. Functions are provided to change the format of duration and date fields.
MySQL Database: The transformed data is stored in a MySQL database. Tables are created to store channel details, playlist details, video details, and comments, allowing for efficient data retrieval and analysis.
Viewing: Users can view the extracted and stored data using the Streamlit application. Options are provided to view home page, extract data, and view insights.
Insights: Insightful questions are provided for users to query the database and gain insights into the YouTube data, such as top videos, channel statistics, comments analysis, etc.
Streamlit App: The project includes a Streamlit web application with a user-friendly interface for data extraction, viewing, and analysis.
Dependencies:

Python 3.7 or higher
pandas
mysql-connector-python
Pillow
google-api-python-client
streamlit
dateutil
Installation:

Clone the repository from GitHub.
Install the dependencies using pip: pip install -r requirements.txt.
Obtain a YouTube Data API key from the Google Cloud Console.
Set up a MySQL database with appropriate privileges.
Update the MySQL connection details and API key in the code.
Run the Streamlit application: streamlit run proj1.py.

Usage:
Run the Streamlit application by executing streamlit run proj1.py in the terminal.
Enter a YouTube channel ID in the "Extract" page and click "Extract Channel Data" to retrieve channel details.
View the extracted data and insights in the Streamlit app.

Contributors:
Vishaali RJ
