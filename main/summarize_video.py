import openai
from googleapiclient.discovery import build
import googleapiclient.discovery
from send_message import ChatBot, MessageComposer
import database
from firebase_admin import db


openai.api_key = 'your-key'
OPENAI_MODEL = 'model'
# tomegavazov
api_key = 'api key'
file_path = 'files/username_to_channel.txt'


class User:
    def __init__(self, username, link):
        self.username = username
        self.link = link
        self.contacted = False


class ChannelCategorizer:

    @staticmethod
    def categorize_entries_by_link_type(users):
        categorized_entries = {
            'channel_name': [],
            'channel_id': [],
            'video_id': []
        }

        for user in users:
            link = user.link
            if link.find('@') != -1 or link.find('youtube.com/c/') != -1:
                categorized_entries['channel_name'].append(user)
            elif link.find('watch?v=') != -1:
                categorized_entries['video_id'].append(user)
            else:
                categorized_entries['channel_id'].append(user)
        return categorized_entries


class ChannelNameExtractor:

    @staticmethod
    def extract_channels(users):
        user_to_channel_name = []

        for user in users:
            username = user.username
            link = user.link

            if link.find("@") != -1:
                user_to_channel_name.append(
                    {'user': username, 'channel_name': '@'+link.split('@')[1].split('/')[0].split('?')[0].split(';')[0]})
            else:
                user_to_channel_name.append(
                    {'user': username, 'channel_name': '@'+link.split('/c/')[1].split('?')[0].split(';')[0]})

        return user_to_channel_name


class ChannelIdExtractor:

    @staticmethod
    def extract_channels(users):
        user_to_channel_id = []
        for user in users:
            username = user.username
            link = user.link

            user_to_channel_id.append(
                {'user': username, 'channel_id': link.split('/')[-1].split(';')[0]})

        return user_to_channel_id


class VideoIdExtractor:

    @staticmethod
    def extract_video_ids(users):
        user_to_video_id = []

        for user in users:
            username = user.username
            link = user.link
            video_id = link.split('v=')[1].split('&')[0].split(';')[0]
            user_to_video_id.append({'user': username, 'video_id': video_id})
        return user_to_video_id


class ChannelIdConverter:

    @staticmethod
    def channel_name_to_channel_id(channel_name):
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=api_key)

        search_response = youtube.search().list(
            q=channel_name,
            type="channel",
            part="id",
            maxResults=1
        ).execute()
        channel_id = search_response["items"][0]["id"]["channelId"]

        return channel_id

    @staticmethod
    def video_id_to_channel_id(video_id):
        youtube = build('youtube', 'v3', developerKey=api_key)

        video_response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()

        channel_id = video_response['items'][0]['snippet']['channelId']
        channel_name = video_response['items'][0]['snippet']['title']
        return channel_id


class LatestVideoExtractor:

    @staticmethod
    def extract_latest_video_by_channel_id(channel_id):

        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=api_key)

        channel_response = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()

        uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        playlist_response = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=1
        ).execute()

        latest_video_id = playlist_response["items"][0]["contentDetails"]["videoId"]
        return latest_video_id


class UserToChannelAggregator:

    @staticmethod
    def aggregate_channels(users):
        categorized_entries = ChannelCategorizer.categorize_entries_by_link_type(
            users)

        user_to_channel_name = ChannelNameExtractor.extract_channels(
            categorized_entries['channel_name'])

        user_to_channel_id = ChannelIdExtractor.extract_channels(
            categorized_entries['channel_id'])
        user_to_video_id = VideoIdExtractor.extract_video_ids(
            categorized_entries['video_id'])

        for entry in user_to_channel_name:
            try:
                converted = {'user': entry['user'], 'channel_id': ChannelIdConverter.channel_name_to_channel_id(
                    entry['channel_name'])}
                user_to_channel_id.append(converted)
            except Exception as e:
                print("Channel doesn't exist error " +
                      str(entry['channel_name']))

        for entry in user_to_video_id:
            try:
                converted = {'user': entry['user'], 'channel_id': ChannelIdConverter.video_id_to_channel_id(
                    entry['video_id'])}
                user_to_channel_id.append(converted)
            except Exception as e:
                print("Channel doesn't exist error " + str(entry['video_id']))

        return user_to_channel_id


def get_users(limit):
    users = db.reference('users')
    uncontacted = []
    for key, user in users.order_by_key().get().items():
        if 'contacted' not in user:
            uncontacted.append(User(user['username'], user['link']))

    return uncontacted[:limit]


def mark_contacted(username):
    user_ref = db.reference('users')
    user_snapshots = user_ref.order_by_child(
        'username').equal_to(username).limit_to_first(10).get()
    for user_snapshot in user_snapshots.items():
        print(user_snapshot)
        key = user_snapshot[0]
        user_data = user_snapshot[1]
        user_data['contacted'] = True
        user_ref.child(key).update(user_data)


if __name__ == '__main__':
    users = get_users(20)
    user_to_channel_id = UserToChannelAggregator.aggregate_channels(users)
    chatbot = ChatBot()

    for entry in user_to_channel_id:
        try:
            latest_video_id = LatestVideoExtractor.extract_latest_video_by_channel_id(
                entry['channel_id'])
            user = entry['user']
            channel_id = entry['channel_id']

            try:
                transcript = MessageComposer.get_transcript(latest_video_id)
                message = MessageComposer.compose_message(
                    transcript, user)
                try:
                    chatbot.send_message_old_acc(
                        user, message.replace("[Your Name]", ''))
                except Exception as e:
                    print(e)
            except Exception as e:
                print('nema transcript za channel ' + str(channel_id))

        except Exception as e:
            print(e)
        finally:
            mark_contacted(entry['user'])
