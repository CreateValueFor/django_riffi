# views.py
import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.music.utils.music_extract import music_extractor
from django.conf import settings
from apps.music.GSEP_LARGE_CLI import Manager, Sender
import time
import os

UPLOAD_SIZE = 1024000000
VALID_DOWNLOAD_TIME = 60

class MusicExtractionAPIView(APIView):
    def post(self, request):
        youtube_url = request.data.get('youtube_url')
        user_id = request.data.get('userid')
        types = request.data.get('output_types').replace(' ','')
        # 1. URL에서 음원 추출 및 저장
        music_file = music_extractor(youtube_url)
        typeList = types.split(',')
        manager = Manager(Sender())
        
        index = 0
        
        start = time.time()
        index = index + 1
        # "downloaded_music/DAY6 ＂HAPPY＂ Lyric Video.wav"
        # "downloaded_music/DAY6 "HAPPY" Lyric Video.wav"

        file = open(music_file, 'rb')
        file_size = os.path.getsize(music_file)
        jobs = []

        for type in typeList:

            # 파일 업로드 전에 미리 presign 하는 과정
            response_data = manager.sender.gsep_initiate(path=music_file, type=type, file_size=file_size, uploadSize=UPLOAD_SIZE)
            if response_data.status_code != 200 or response_data.json().get('resultCode') != 1000:
                print(" Error [%s]" % (response_data.text))
                continue
            gsep_job_id = response_data.json().get('resultData').get("gsepId")
            pre_signed_url_list = response_data.json().get('resultData').get("preSignedUrl")
            chunk_size = response_data.json().get('resultData').get("uploadSize")

            upload_count = 0
            multi_upload_array = []
            file = open(music_file, 'rb')
            for piece1G in manager.read_in_chunks(file_object=file, chunk_size=chunk_size):
                print("request uploading %s %s/%s" % (type, upload_count + 1 , len(pre_signed_url_list)))
                pre_signed_url = pre_signed_url_list[upload_count]
                upload_count = upload_count + 1
                etag_header = manager.sender.upload_file_to_s3(preSignedUrl=pre_signed_url, file=piece1G)
                multi_upload_array.append({'awsETag': etag_header, 'partNumber': upload_count})
            file.close()
            jobs.append({
                "jobs": gsep_job_id,
                "multi_upload_array" : multi_upload_array,
                "status":None
            })
        file.close()

        print(jobs)

        completed_url_list= []
        all_done = False
        while not all_done:
            all_done = True
            for job_item  in  jobs:
                if job_item["status"] != "done":
                    response_status_data = manager.sender.gsep_status(gsep_job_id=job_item["jobs"], multi_upload_array=job_item["multi_upload_array"], valid_download_time=VALID_DOWNLOAD_TIME)
                    if response_status_data.status_code != 200 or response_status_data.json().get('resultCode') != 1000:
                        print(" Error [%s]" % (response_status_data.text))
                        break
                    # response 비구조화
                    status = response_status_data.json().get('resultData').get("status")
                    completed_url = response_status_data.json().get('resultData').get("downloadUrl")
                    print("request status - time[%ss] status[%s]" % ( time.time() - start, status))
                    if status == 'done' or status == 'fail':
                        job_item["status"] = "done"
                        completed_url_list.append(completed_url)
                        print(" completed - time[%ss] url[%s]" % (time.time() - start, completed_url))
                    else:
                        all_done=False
            time.sleep(10)
        
        return Response({'status': 'success', 'download_url': completed_url_list}, status=200)
        
        # 3. 데이터베이스에 Music 레코드 생성
        # try:
            # user = User.objects.get(id=user_id)
            # music = Music.objects.create(user=user, download_url=download_url)
        
        # except User.DoesNotExist:
            # return Response({'status': 'error', 'message': 'User not found'}, status=404)