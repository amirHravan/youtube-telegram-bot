import os
import logging
from telegram.ext import Updater, CommandHandler
import requests
from pytube import YouTube, Playlist
import dotenv

dotenv.load_dotenv()
resolution_order = ['480p', '360p']
WHITE_LIST = [
    140770223,
    745585668
]


def start_command_handler(update, context):
    if update.message.chat_id not in WHITE_LIST:
        return
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Hello! Send me a YouTube link to download and upload it.")


def help_command_handler(update, context):
    if update.message.chat_id not in WHITE_LIST:
        return
    context.bot.send_message(chat_id=update.message.chat_id, text="""
        use following commands for using the bot:
        
        /vid YOUTUBE_VIDEO_LINK -> download youtube video
        /playlist YOUTUBE_PLAYLIST_LINK -> download all youtube playlist
        /vid_info YOUTUBE_VIDEO_LINK -> information about video
        /help -> see this message again
        
        have fun.
    """)


def get_video_thumbnail(youtube):
    thumb_path = f'/root/Documents/YoutubeTelegramBot/thumbnail/{youtube.title}.jpg'
    with open(thumb_path, 'wb') as image:
        response = requests.get(youtube.thumbnail_url)
        if response.status_code:
            image.write(response.content)
        else:
            return None
    return thumb_path


def send_video_info(update, context, youtube):
    thumbnail_path = get_video_thumbnail(youtube)
    if thumbnail_path is None:
        thumbnail_path = f'/root/Documents/YoutubeTelegramBot/thumbnail/not_found.jpg'
    caption = get_video_caption(youtube)
    send_photo(update, context, thumbnail_path, caption)


def info_command_handler(update, context):
    if update.message.chat_id not in WHITE_LIST:
        return
    link = update.message.text
    videos = []
    try:
        if '/playlist' in link:
            vid_links = Playlist(link).video_urls
            for vid_link in vid_links:
                videos.append(YouTube(vid_link))
        else:
            videos.append(YouTube(link))
        for youtube in videos:
            send_video_info(update, context, youtube)
        videos.clear()
    except Exception as e:
        send_error(update, context, str(e))


def send_error(update, context, message):
    logging.error(f"Error occurred: {message}")
    context.bot.send_message(chat_id=update.message.chat_id, text=message)


def download_video(youtube):
    video = youtube.streams.get_lowest_resolution()
    for res in resolution_order:
        video = youtube.streams.get_by_resolution(res)
        if video:
            break
    video.download(output_path="vids/")
    return f'vids/{video.default_filename}'


def send_photo(update, context, photo_path, caption):
    with open(photo_path, 'rb') as img:
        context.bot.send_photo(chat_id=update.message.chat_id, photo=img, caption=caption)


def send_video(update, context, video_path, caption):
    with open(video_path, 'rb') as video:
        bot = context.bot
        chat_id = update.message.chat_id
        bot.send_video(chat_id=chat_id, video=video, caption=caption)


def get_video_caption(youtube: YouTube):
    date = youtube.publish_date.strftime('%Y/%m/%d')
    return f'''
📚   {youtube.title}
📅   {date}
👀   {youtube.views}
✍️  {youtube.author}
    '''


def download_and_send_video(update, context, url):
    try:
        youtube = YouTube(url)
        video_path = download_video(youtube)
        caption = get_video_caption(youtube)
        send_video(update, context, video_path, caption)
        os.remove(video_path)
    except Exception as e:
        send_error(update, context, str(e))


def video_download_command_handler(update, context):
    if update.message.chat_id not in WHITE_LIST:
        return
    url = update.message.text
    if url == '':
        return
    download_and_send_video(update, context, url)


def playlist_download_command_handler(update, context):
    if update.message.chat_id not in WHITE_LIST:
        return
    playlist_url = update.message.text
    playlist = Playlist(playlist_url)
    urls = playlist.video_urls
    for url in urls:
        if url == '':
            return
        download_and_send_video(update, context, url)


def main():
    bot_token = os.environ['TELEGRAM_TOKEN']
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start_command_handler))
    dispatcher.add_handler(CommandHandler('vid', video_download_command_handler))
    dispatcher.add_handler(CommandHandler('playlist', playlist_download_command_handler))
    dispatcher.add_handler(CommandHandler('vid_info', info_command_handler))
    dispatcher.add_handler(CommandHandler('help', help_command_handler))

    updater.start_polling()


if __name__ == '__main__':
    main()
