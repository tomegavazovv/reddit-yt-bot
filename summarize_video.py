import openai
from youtube_transcript_api import YouTubeTranscriptApi as yta
from googleapiclient.discovery import build
import googleapiclient.discovery
from send_message import ChatBot


openai.api_key = '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'
OPENAI_MODEL = 'text-davinci-003'
api_key = 'AIzaSyBDAWuQwQecoRS6SlnRL4cml-aCOBufii4'
file_path = 'username_to_channel.txt'


class ChannelCategorizer:

    @staticmethod
    def categorize_entries_by_link_type(entries):
        categorized_entries = {
            'channel_name': [],
            'channel_id': [],
            'video_id': []
        }

        for entry in entries:
            link = entry.split(':')[2]
            if link.find('@') != -1 or link.find('youtube.com/c/') != -1:
                categorized_entries['channel_name'].append(entry)
            elif link.find('watch?v=') != -1:
                categorized_entries['video_id'].append(entry)
            else:
                categorized_entries['channel_id'].append(entry)
        return categorized_entries


class ChannelNameExtractor:

    @staticmethod
    def extract_channels(entries):
        user_to_channel_name = []

        for entry in entries:

            user = entry.split(':')[0]

            if entry.find("@") != -1:
                user_to_channel_name.append(
                    {'user': user, 'channel_name': '@'+entry.split('@')[1].split('/')[0].split('?')[0].split(';')[0]})
            else:
                user_to_channel_name.append(
                    {'user': user, 'channel_name': '@'+entry.split('/c/')[1].split('?')[0].split(';')[0]})

        return user_to_channel_name


class ChannelIdExtractor:

    @staticmethod
    def extract_channels(entries):
        user_to_channel_id = []
        for entry in entries:
            user = entry.split(':')[0]

            user_to_channel_id.append(
                {'user': user, 'channel_id': entry.split('/')[-1].split(';')[0]})

        return user_to_channel_id


class VideoIdExtractor:

    @staticmethod
    def extract_video_ids(entries):
        user_to_video_id = []

        for entry in entries:
            user = entry.split(":")[0]
            link = entry.split(":")[2]
            video_id = link.split('v=')[1][:-2]
            user_to_video_id.append({'user': user, 'video_id': video_id})
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
    def aggregate_channels(entries):
        categorized_entries = ChannelCategorizer.categorize_entries_by_link_type(
            entries)

        user_to_channel_name = ChannelNameExtractor.extract_channels(
            categorized_entries['channel_name'])

        user_to_channel_id = ChannelIdExtractor.extract_channels(
            categorized_entries['channel_id'])
        user_to_video_id = VideoIdExtractor.extract_video_ids(
            categorized_entries['video_id'])

        for entry in user_to_channel_name:
            converted = {'user': entry['user'], 'channel_id': ChannelIdConverter.channel_name_to_channel_id(
                entry['channel_name'])}
            user_to_channel_id.append(converted)

        for entry in user_to_video_id:
            converted = {'user': entry['user'], 'channel_id': ChannelIdConverter.video_id_to_channel_id(
                entry['video_id'])}
            user_to_channel_id.append(converted)

        return user_to_channel_id


def read_lines(limit):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    return lines[:limit]


class MessageComposer:

    @staticmethod
    def get_transcript(video_id):
        data = yta.get_transcript(video_id)
        transcript = ''

        for value in data:
            for key, val in value.items():
                if key == 'text':
                    transcript += val
                    l = transcript.splitlines()

        return ' '.join(l)[:5000]

    @staticmethod
    def compose_message(transcript, user):
        system_prompt = "I would like for you to assume the role of a Cold Email Expert"
        with open('prompt_without_ad.txt', 'r') as prompt:
            user_prompt = prompt.read()
        user_prompt = user_prompt.replace(
            '{user}', user).replace('{transcript}', transcript)

        response = openai.chat.completions.create(
            model='gpt-3.5-turbo-16k',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            max_tokens=4096,
            temperature=1
        )

        return response.choices[0].message.content


if __name__ == '__main__':
    entries = read_lines(10)
    user_to_channel_id = UserToChannelAggregator.aggregate_channels(entries)
    chatbot = ChatBot()

    for entry in user_to_channel_id:
        try:
            latest_video_id = LatestVideoExtractor.extract_latest_video_by_channel_id(
                entry['channel_id'])

            transcript = MessageComposer.get_transcript(latest_video_id)

            message = MessageComposer.compose_message(
                transcript, entry['user'])
            try:
                chatbot.send_message_old_acc(entry['user'], message)
            except Exception as e:
                print(e)

        except Exception as e:
            print('nema video ili transcript za ' + str(entry['user']))
