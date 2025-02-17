#Importing Libraries
from googleapiclient.discovery import build  
import mysql.connector
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from dateutil import parser
import plotly.express as px

#Api connection
def api_connect():
    api_service_name = 'youtube'
    api_version = 'v3'
    api_key = ' ' 
    youtube = build(api_service_name,api_version,developerKey=api_key)
    return youtube
youtube = api_connect()

#MySQL connector
myDb = mysql.connector.connect(
    host = 'localhost', #SQL connection requirements
    user = 'root', 
    password = '', 
    database = 'yt_data_cap1'
)
myCursor = myDb.cursor()

#Changing Duration format
def durationInSeconds(duration):
    duration =list(duration)
    del duration[0:2]
    duration_seconds = 0
    for i,e in enumerate(duration):
        if(e == 'H'):
            duration_seconds += int(duration[i-1])* 60 * 60
        elif(e == 'M'):
            duration_seconds += int(duration[i-1])* 60
        elif(e == 'S'):
            duration_seconds += int(duration[i-1])
    return duration_seconds

#Changing Date format
def changeDateFormat(date_string):
    datetime_obj = parser.isoparse(date_string)
    format_datetime = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
    return format_datetime

#Getting Channel Information
def get_channel_details(channel_id):
    request = youtube.channels().list(
        id = channel_id,
        part = 'snippet,contentDetails,statistics,status'
        )
    response = request.execute()

    for i in response['items']:
        data = dict(           
            channel_id = i['id'],
            channel_name = i['snippet']['title'],
            sub_count = i['statistics']['subscriberCount'],
            view_count = i['statistics']['viewCount'],
            videos_count = i['statistics']['videoCount'],
            channel_description = i['snippet']['description'],
            playlist_id = i['contentDetails']['relatedPlaylists']['uploads'],
            channel_status = i['status']['privacyStatus']
            )
    return data

#To get Video Id's
def get_video_ids(channel_id):
    channel_details = get_channel_details(channel_id)
    unique_playlist_id = channel_details['playlist_id']
    video_ids = []
    nextPageToken = None
    while True:
        response = youtube.playlistItems().list(
            playlistId = unique_playlist_id, 
            part = 'snippet,id',
            maxResults = 50,
            pageToken = nextPageToken
        ).execute()
        for item in response['items']:
            video_ids.append(item['snippet']['resourceId']['videoId'])
        nextPageToken = response.get('nextPageToken')
        if(nextPageToken is None):
            break
    return video_ids

#To get video details         
def get_video_details(video_ids):
    video_details = []  
 
    for i in range(0, len(video_ids), 50):
        response = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i + 50])).execute()
        for item in response['items']:
            data = dict(
                video_id = item.get('id'),
                channel_id = item['snippet'].get('channelId'), 
                video_name = item['snippet'].get('title'),
                video_description = item['snippet'].get('description'),
                published_date = item['snippet'].get('publishedAt'),
                view_count = item['statistics'].get('viewCount'),
                like_count = item['statistics'].get('likeCount'),
                favorite_count = item['statistics'].get('favoriteCount'),
                comment_count = item['statistics'].get('commentCount'),
                duration = item['contentDetails'].get('duration') ,                
                thumbnail = item['snippet']['thumbnails']['default']['url'],                
                caption_status = item['contentDetails'].get('caption')                
            )
            date_string = data['published_date'] 
            date_string = changeDateFormat(date_string)
            data['published_date'] = date_string
            duration = data['duration']
            duration = durationInSeconds(duration)
            data['duration'] = duration                
            video_details.append(data)
    return video_details

# To get Playlist details
def get_playlist_details(channel_id):
    nextPageToken = None
    playlist_details = []
    
    while True:
        response = youtube.playlists().list(
            channelId = channel_id,
            part = 'snippet,contentDetails',
            maxResults = 50,
            pageToken = nextPageToken
        ).execute()
        for item in response['items']:
            data = dict(
                playlist_id = item.get('id'),
                channel_id = item['snippet'].get('channelId'),
                playlist_name = item['snippet'].get('title'),
                video_count = item['contentDetails'].get('itemCount')
                )
            playlist_details.append(data)
        nextPageToken = response.get('nextPageToken')
        if(nextPageToken is None):
            break
    return playlist_details

# To get Comment details
def get_comment_details(video_ids):
    try:        
        comment_details = []
        for video_id in video_ids:
            nextPageToken = None
            while True:            
                response = youtube.commentThreads().list(
                    videoId = video_id,
                    part = 'snippet',
                    maxResults = 100,
                    pageToken = nextPageToken                        
                    ).execute()
                for item in response['items']:
                    data = dict(
                        comment_id = item.get('id'),
                        video_id = item['snippet'].get('videoId'),
                        comment_text = item['snippet']['topLevelComment']['snippet'].get('textDisplay'),
                        comment_author = item['snippet']['topLevelComment']['snippet'].get('authorDisplayName'),
                        comment_published_date =  item['snippet']['topLevelComment']['snippet'].get('publishedAt')
                    )
                    comment_details.append(data)
                nextPageToken = response.get('nextPageToken')
                if(nextPageToken is None):
                    break
    except Exception as err:
        print(err)
        pass
    return  comment_details

#Creating Tables in MYSQL
def create_tables():
    myCursor.execute("Create Table IF NOT EXISTS Channel (channel_id varchar(255) PRIMARY KEY, channel_name varchar(255) NOT NULL, sub_count int, channel_views int, channel_description text,channel_status varchar(255))")
    myCursor.execute("Create Table IF NOT EXISTS Playlist (playlist_id varchar(255) PRIMARY KEY, channel_id varchar(255) NOT NULL,playlist_name varchar(255),video_count int, FOREIGN KEY (channel_id) REFERENCES Channel(channel_id))")
    myCursor.execute("Create Table IF NOT EXISTS Video (video_id varchar(255) PRIMARY KEY, channel_id varchar(255) NOT NULL, video_name varchar(255), video_description text, published_date datetime, view_count int, like_count int, favorite_count int, comment_count int, duration int, thumbnail varchar(255), caption_status varchar(255), FOREIGN KEY (channel_id) REFERENCES Channel(channel_id))")
    myCursor.execute("Create Table IF NOT EXISTS Comment (comment_id varchar(255) PRIMARY KEY, video_id varchar(255) NOT NULL,comment_text text, comment_author varchar(255),comment_published_date datetime,FOREIGN KEY (video_id) REFERENCES Video(video_id))")
    myDb.commit()

#Viewing tables in UI
def show_table(table):    
    if(table == ':blue[Channels]'):
        show_channel_table()        
    elif(table == ':blue[Videos]'):
        show_video_table()
    elif(table == ':blue[Playlists]'):
        show_playlist_table()
    elif(table == ':blue[Comments]'):
        show_comment_table()
        
def show_channel_table():
    myCursor.execute('Select * from Channel')
    myResult = myCursor.fetchall()
    df = pd.DataFrame(data = myResult, columns = myCursor.column_names)
    st.table(df)

def show_video_table():
    myCursor.execute('Select * from Video')
    myResult = myCursor.fetchall()
    df = pd.DataFrame(data = myResult, columns = myCursor.column_names)
    st.table(df)

def show_playlist_table():
    myCursor.execute('Select * from Playlist')
    myResult = myCursor.fetchall()
    df = pd.DataFrame(data = myResult, columns = myCursor.column_names)
    st.table(df)
    
def show_comment_table():
    myCursor.execute('Select * from Comment')
    myResult = myCursor.fetchall()
    df = pd.DataFrame(data = myResult, columns = myCursor.column_names)
    st.table(df)

# Inserting data to MYSQL
def insert_all_table(channel_id):
    insert_channel_details(channel_id) 
    insert_playlist_details(channel_id)
    insert_video_details(channel_id) 
    insert_comment_details(channel_id)
          
def insert_channel_details(channel_id):
    channel_details = get_channel_details(channel_id)
    channel_details = (channel_details['channel_id'],channel_details['channel_name'],channel_details['sub_count'],channel_details['view_count'],channel_details['channel_description'],channel_details['channel_status'],)
    insert_query = '''INSERT INTO Channel 
                    VALUES(%s,%s,%s,%s,%s,%s)''' 
    myCursor.execute(insert_query,channel_details)
    myDb.commit()
    print(myCursor.rowcount,'rows insterted successfully')
   
def insert_playlist_details(channel_id):
    try:        
        playlist_details = get_playlist_details(channel_id)
        for playlist_detail in playlist_details:            
            playlist_detail = (playlist_detail['playlist_id'],playlist_detail['channel_id'],playlist_detail['playlist_name'],playlist_detail['video_count'])
            insert_query = '''INSERT INTO Playlist 
                            VALUES(%s,%s,%s,%s)''' 
            myCursor.execute(insert_query,playlist_detail)
            myDb.commit()
    except Exception as err:
        print(err) 
        pass

def insert_video_details(channel_id):
    try:
        video_ids = get_video_ids(channel_id)        
        video_details = get_video_details(video_ids)        
        for video_detail in video_details:
            video_detail = (video_detail['video_id'],video_detail['channel_id'],video_detail['video_name'],video_detail['video_description'],video_detail['published_date'],video_detail['view_count'],video_detail['like_count'],video_detail['favorite_count'],video_detail['comment_count'],video_detail['duration'],video_detail['thumbnail'],video_detail['caption_status'])
            insert_query = '''INSERT INTO Video 
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            myCursor.execute(insert_query,video_detail)
            myDb.commit()
    except Exception as err:
        print(err)        
        
def insert_comment_details(channel_id):
    try:        
        video_ids = get_video_ids(channel_id)
        comment_details = get_comment_details(video_ids)
        for comment_detail in comment_details:
            date_string = comment_detail['comment_published_date'] 
            date_string = changeDateFormat(date_string)
            comment_detail['comment_published_date'] = date_string
            comment_detail = (comment_detail['comment_id'],comment_detail['video_id'],comment_detail['comment_text'],comment_detail['comment_author'],comment_detail['comment_published_date'])
            insert_query = '''INSERT INTO Comment 
            VALUES(%s,%s,%s,%s,%s)''' 
            myCursor.execute(insert_query,comment_detail)
            myDb.commit()
    except Exception as err:
        print(err) 
        pass
    
# Streamlit UI part 
# Add your Streamlit app content here
st.title("My Streamlit App 🜲")

# Side Navigaton bar
with st.sidebar:
    selected = option_menu(
       menu_title = None,
       options= ["Home","YT Details","Add Data to DB","View Tables","SQL Query"],
       icons = ['house', 'play', 'cloud-upload', "list-task", 'gear'],
       menu_icon = 'cast',
    )

#Home UI
if selected == "Home":
    st.image(r"C:\Users\Vishaali Naagaarjun\OneDrive\Pictures\yt.jpg")
    col1,col2 = st.columns(2,gap= 'medium')
    col1.markdown("## :blue[Domain] : Social Media")
    col1.markdown("## :green[Technologies used] : Python, Youtube Data API, MySql, Streamlit")
    col1.markdown("## :red[Overview] : Retrieving the Youtube channels data from the Google API, migrating and transforming data into a SQL database,then querying the data and displaying it in the Streamlit app.")
    col2.markdown("#   ")
    col2.markdown("#   ")
    col2.markdown("#   ")
    
if selected == "YT Details":
    st.subheader(":green[Enter Channel ID]")
    channel_id = st.text_input('Channel ID]"',label_visibility = 'collapsed')
    if st.button (' :blue[View Channel Details]'):
        try:
            df = get_channel_details(channel_id)
            st.dataframe(df)
        except:
            st.warning('Please enter a valid Channel ID')

    if st.button(':blue[View Video Details]'):
        try:
            with st.spinner('Please Wait for it...'):
                video_ids = get_video_ids(channel_id)
                df = get_video_details(video_ids)
                st.dataframe(df)
        except: 
            st.warning('Please enter a valid Channel ID')

    if st.button(' :blue[View Playlist Details]'):
        try:
            df = get_playlist_details(channel_id)
            st.dataframe(df)
        except:
            st.warning('Please enter a valid Channel ID')
        
#Add Data to Database UI           
elif selected == 'Add Data to DB':
    st.subheader(":green[Enter Channel ID]")
    channel_id = st.text_input(' Enter Channel Id', label_visibility = 'collapsed')
    if st.button(':blue[Collect and Store Channel data]'):        
        create_tables()
        ch_ids = []
        myCursor.execute('Select channel_id from Channel')
        myResult = myCursor.fetchall()   
        
        for i in myResult:
            ch_ids.append(i[0])
        if(channel_id in ch_ids):
            st.success('Channel Data already Available in SQL')
        elif(channel_id == ''):
            st.warning('Invalid Channel Id')
        else:
            with st.spinner('Please Wait as it may take a few minutes...'):
                try:
                    insert_all_table(channel_id)
                    st.success('Data has been insterted')
                except:
                    
                    st.warning('Invalid Channel Id')  

# View Tables UI
elif selected == 'View Tables':
    st.subheader(":green[Select the table to be viewed from SQL Database]")
    view_table = st.radio('Select the table to view from MySql',
                          [':blue[Channels]',':blue[Videos]',':blue[Playlists]',':blue[Comments]'],
                          label_visibility = 'collapsed',horizontal = True)
    show_table(view_table)

#SQL Query UI
elif selected == 'SQL Query':
    st.subheader(" :green[Please select a below query to execute()]")
    questions = st.selectbox(':blue[Queries]',
                            ['1. What are the names of all the videos and their corresponding channels?',
                            '2. Which channels have the most number of videos, and how many videos do they have?',
                            '3. What are the top 10 most viewed videos and their respective channels?',
                            '4. How many comments were made on each video, and what are their corresponding video names?',
                            '5. Which videos have the highest number of likes, and what are their corresponding channel names?',
                            '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?',
                            '7. What is the total number of views for each channel, and what are their corresponding channel names?',
                            '8. What are the names of all the channels that have published videos in the year 2022?',
                            '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
                            '10. Which videos have the highest number of comments, and what are their corresponding channel names?'])

    if questions == '1. What are the names of all the videos and their corresponding channels?':
        myCursor.execute('''SELECT Video.video_name AS Video_Title,Channel.channel_name AS Channel_Name FROM Video
                            LEFT JOIN Channel
                            ON Video.channel_id = Channel.channel_id;
                            ''')
        df = pd.DataFrame(myCursor.fetchall(), columns=myCursor.column_names)
        st.write(df)

    elif questions == '2. Which channels have the most number of videos, and how many videos do they have?':
        myCursor.execute("""SELECT Channel.channel_name Channel_Name,COUNT(Video.video_id) AS Video_Count FROM Video
                            RIGHT JOIN Channel
                            ON Video.channel_id = Channel.channel_id
                            GROUP BY channel.channel_id
                            ORDER BY video_count DESC;
                            """)
        df = pd.DataFrame(myCursor.fetchall(), columns=myCursor.column_names)
        st.write(df)
        fig = px.bar(df, x=myCursor.column_names[0], y=myCursor.column_names[1], orientation='v', color=myCursor.column_names[0])
        st.plotly_chart(fig, use_container_width=True)

    elif questions == '3. What are the top 10 most viewed videos and their respective channels?':
        myCursor.execute("""SELECT  Channel.channel_name Channel_Name, Video.view_count View_Count, Video.video_name Video_Name FROM Video
                            RIGHT JOIN Channel
                            ON Video.channel_id = Channel.channel_id
                            ORDER BY view_count DESC
                            LIMIT 10;
                            """)
        df = pd.DataFrame(myCursor.fetchall(), columns=myCursor.column_names)
        st.write(df)
        fig = px.bar(df, x=myCursor.column_names[2], y=myCursor.column_names[1], orientation='h', color=myCursor.column_names[0])
        st.plotly_chart(fig, use_container_width=True)

    elif questions == '4. How many comments were made on each video, and what are their corresponding video names?':
        myCursor.execute("""SELECT Video.video_id Video_Id, video.video_name Video_Name,COUNT(comment_id) AS Comment_Count FROM Comment
                            LEFT JOIN Video
                            ON Comment.video_id = Video.video_id
                            GROUP BY Video.video_id
                            ORDER BY comment_count DESC;
                            """)
        df = pd.DataFrame(myCursor.fetchall(), columns=myCursor.column_names)
        st.write(df)

    elif questions == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
        myCursor.execute("""SELECT  Channel.channel_name Channel_Name, Video.like_count Likes, Video.video_name Video_Name FROM Video
                            RIGHT JOIN Channel
                            ON Video.channel_id = Channel.channel_id
                            ORDER BY like_count DESC;
                            """)
        df = pd.DataFrame(myCursor.fetchall(), columns=myCursor.column_names)
        st.write(df)
        fig = px.bar(df, x=myCursor.column_names[2], y=myCursor.column_names[1], orientation='h', color=myCursor.column_names[0])
        st.plotly_chart(fig, use_container_width=True)
    
    elif questions == '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?':
        myCursor.execute("""SELECT video_name Video_Name, like_count Likes FROM Video
                            ORDER BY like_count DESC;
                            """)
        df = pd.DataFrame(myCursor.fetchall(), columns=myCursor.column_names)
        st.write(df)

    elif questions == '7. What is the total number of views for each channel, and what are their corresponding channel names?':
        myCursor.execute("""SELECT channel_name Channel_Name, channel_views AS View_Count
                            FROM Channel
                            ORDER BY view_count DESC;""")
        df = pd.DataFrame(myCursor.fetchall(), columns=myCursor.column_names)
        st.write(df)
        fig = px.bar(df, x=myCursor.column_names[0], y=myCursor.column_names[1], orientation='v', color=myCursor.column_names[0])
        st.plotly_chart(fig, use_container_width=True)

    elif questions == '8. What are the names of all the channels that have published videos in the year 2022?':
        myCursor.execute("""SELECT  Channel.channel_name Channel_Name,Video.video_name Video_Name ,Video.published_date Published_Date FROM Video 
                            LEFT JOIN Channel 
                            ON Video.channel_id = Channel.channel_id
                            WHERE Video.published_date LIKE '2022%';
                            """)
        df = pd.DataFrame(myCursor.fetchall(), columns=myCursor.column_names)
        st.write(df)
    
    elif questions == '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
        myCursor.execute("""SELECT Channel.channel_name Channel_Name ,ROUND(AVG(Video.duration)/ 60,2) as 'Duration in Minutes' FROM Video
                            RIGHT JOIN Channel
                            ON Video.channel_id = Channel.channel_id
                            GROUP BY channel.channel_id
                            ORDER BY 'Duration in Minutes' DESC;
                            """)
        df = pd.DataFrame(myCursor.fetchall(), columns=myCursor.column_names)
        st.write(df)
        fig = px.bar(df, x=myCursor.column_names[0], y=myCursor.column_names[1], orientation='v', color=myCursor.column_names[0])
        st.plotly_chart(fig, use_container_width=True)
    
    elif questions == '10. Which videos have the highest number of comments, and what are their corresponding channel names?':
        myCursor.execute("""SELECT Channel.channel_name Channel_Name,video.video_name Video_Name, COUNT(comment_id) AS Comment_Count FROM Comment
                            Left JOIN Video ON Comment.video_id = Video.video_id
                            inner JOIN CHANNEL ON Video.channel_id = Channel.channel_id
                            GROUP BY Video.video_id
                            ORDER BY comment_count DESC
                            """)
        df = pd.DataFrame(myCursor.fetchall(), columns=myCursor.column_names)
        st.write(df)
        fig = px.bar(df, x=myCursor.column_names[1], y=myCursor.column_names[2], orientation='v', color=myCursor.column_names[0])
        st.plotly_chart(fig, use_container_width=True)







    
    
        
        
    





