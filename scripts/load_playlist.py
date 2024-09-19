import pandas as pd
import json

from app_1.models import Playlist, Playlistvideos, Video

def run():
    yt_playlist = ""

    Playlist.objects.all().delete()
    Playlistvideos.objects.all().delete()
    
    with open(yt_playlist, 'r') as fin:
        for ind, line in enumerate(fin):
            if line != '':
                line = json.loads(line)
                playlist_name = line['playlist_name'] 
                playlist_url = line['playlist_url'] 
                video_list = line['playlist_vids'] 
            
                p = Playlist(playlist_name=playlist_name, 
                            playlist_url=playlist_url) 
                p.save()

                for vid in video_list:
                    vid_filter = Video.objects.filter(videourl=vid)

                    vid_obj = vid_filter.first()

                    if vid_obj:
                        v = Playlistvideos(playlist=p,
                                       video=vid_obj)
                        v.save()
