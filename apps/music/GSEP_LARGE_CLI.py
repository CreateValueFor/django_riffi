import hashlib
import hmac
import base64
import requests
import os
import argparse
import time


class Sender:
    def __init__(self):

        self.server = "https://openapi.gaudiolab.io"
        self.secret_key = "m+sfe73a"
        self.access_key = "3JLS0X0Q2CEYj5wIw0ha"

    def get_signature(self, method, timestamp, api):
        msg = ''
        msg += method
        msg += " "
        msg += api
        msg += "\n"
        msg += timestamp
        msg += "\n"
        msg += self.access_key
        signature = base64.b64encode(hmac.new(bytes(self.secret_key, encoding="utf-8"), bytes(msg, encoding="utf-8"),
                                              digestmod=hashlib.sha256).digest()).decode()
        print(str(signature))
        return str(signature)

    def gsep_initiate(self, path='', type='voclas', file_size=1024, uploadSize=1024000000):
        print("input type ===== {}".format(type))
        timestamp = str(int(round(time.time() * 1000)))
        api = "/api/v1/gsep/large/init"
        url = self.server + api
        headers = {'x-ga-timestamp': timestamp,
                   'x-ga-access-key': self.access_key,
                   'x-ga-signature': self.get_signature(method="POST", timestamp=timestamp, api=api),
                   }
        payload = {
            'name': os.path.basename(path),
            'type': type,
            'fileSize': file_size,
            'uploadSize': uploadSize,
        }
        response_data = requests.post(url, headers=headers, json=payload)
        return response_data

    def upload_file_to_s3(self, preSignedUrl='', file=''):
        response_data = requests.put(preSignedUrl, data=file)
        etagHeader = response_data.headers.get('ETag').replace("\"", "")
        return etagHeader

    def gsep_status(self, gsep_job_id, multi_upload_array=[], valid_download_time=1):
        timestamp = str(int(round(time.time() * 1000)))
        api = "/api/v1/gsep/large/status"
        url = self.server + api
        headers = {'x-ga-timestamp': timestamp,
                   'x-ga-access-key': self.access_key,
                   'x-ga-signature': self.get_signature(method="POST", timestamp=timestamp, api=api),
                   }
        payload = {
            'gsepJobId': gsep_job_id,
            'parts': multi_upload_array,
            'validDownloadTime': valid_download_time
        }
        response_data = requests.post(url, headers=headers, json=payload)
        return response_data


class Manager:
    def __init__(self, sender):
        self.supported_audio_extensions = [".wav", ".mp3", ".m4a", ".mp4", ".flac"]
        self.sender = sender

    def get_gsep_files(self, folder):
        print('START - Folder[%s]' % (folder))
        folder_list = os.listdir(folder)
        ret_availed_files = []
        for file in folder_list:
            file_type = os.path.splitext(os.path.basename(file))[1]
            file_type_check_result = file_type in self.supported_audio_extensions
            if file_type_check_result is True:
                ret_availed_files.append(str(folder + "/" + file))

        return ret_availed_files

    def read_in_chunks(self, file_object, chunk_size=1024 * 100000):
        while True:
            data = file_object.read(chunk_size)
            if not data:
                break
            yield data


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        '-i', '--input-path',
        type=str,
        required=True,
        help="Input file folder path"
    )
    arg_parser.add_argument(
        '-t', '--output_type',
        type=str,
        required=True,
        default='vocals',
        help="Output Result[vocals, drums, bass, accom]"
    )
    args = arg_parser.parse_args()
    audio_path = args.input_path
    type = args.output_type
    manager = Manager(Sender())
    audio_list = manager.get_gsep_files(folder=audio_path)

    upload_size = 1024000000
    valid_download_time = 60
    index = 0
    for item in audio_list:
        start = time.time()
        index = index + 1
        print("[%s/%s] request initiate -  %s" % (index, len(audio_list), item))
        print(item)
        file = open(item, 'rb')
        file_size = os.path.getsize(item)
        response_data = manager.sender.gsep_initiate(path=item, type=type, file_size=file_size, uploadSize=upload_size)
        if response_data.status_code != 200 or response_data.json().get('resultCode') != 1000:
            print(" Error [%s]" % (response_data.text))
            continue

        gsep_job_id = response_data.json().get('resultData').get("gsepId")
        pre_signed_url_list = response_data.json().get('resultData').get("preSignedUrl")
        chunk_size = response_data.json().get('resultData').get("uploadSize")

        upload_count = 0
        multi_upload_array = []
        for piece1G in manager.read_in_chunks(file_object=file, chunk_size=chunk_size):
            print("[%s/%s] request uploading %s/%s" % (index, len(audio_list), upload_count + 1 , len(pre_signed_url_list)))
            pre_signed_url = pre_signed_url_list[upload_count]
            upload_count = upload_count + 1
            etag_header = manager.sender.upload_file_to_s3(preSignedUrl=pre_signed_url, file=piece1G)
            multi_upload_array.append({'awsETag': etag_header, 'partNumber': upload_count})
        file.close()

        while True:
            response_status_data = manager.sender.gsep_status(gsep_job_id=gsep_job_id, multi_upload_array=multi_upload_array, valid_download_time=valid_download_time)
            if response_status_data.status_code != 200 or response_status_data.json().get('resultCode') != 1000:
                print(" Error [%s]" % (response_status_data.text))
                break
            status = response_status_data.json().get('resultData').get("status")
            completed_url = response_status_data.json().get('resultData').get("downloadUrl")
            print("[%s/%s] request status - time[%ss] status[%s]" % (index, len(audio_list), time.time() - start, status))
            if status == 'done' or status == 'fail':
                print("[%s/%s] completed - time[%ss] url[%s]" % (index, len(audio_list), time.time() - start, completed_url))
                break
            time.sleep(10)