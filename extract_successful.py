from googleapiclient.discovery import build


api_key = 'AIzaSyAemp7FObIIXrA1TuzAZon65sB2W2FxAYA'


def find_channel_id_by_channel_name(channel_name):
    youtube = build('youtube', 'v3', developerKey=api_key)

    search_response = youtube.search().list(
        q=channel_name,
        type="channel",
        part="id",
        maxResults=1
    ).execute()

    channel_id = search_response["items"][0]["id"]["channelId"]
    return channel_id


if __name__ == '__main__':

    with open('mailchimp.exe') as mailchimp:
        for line in mailchimp.readlines():
            channel_name = line['channel']
            channel_id = find_channel_id_by_channel_name(channel_name)
