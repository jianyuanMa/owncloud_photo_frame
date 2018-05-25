import owncloud
import os
import logging
import threading
import time
from config import Config

class OwnCloudClient(threading.Thread):
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.client = owncloud.Client(Config['owncloud_url'])
        self.client.login(Config['owncloud_login'], Config['owncloud_password'])
        self.stopped = event

    def downloadPhoto(self, downloadList):
        for photo in downloadList:
            photoName=photo.split('/')[2]
            filename = 'images/'+photoName
            self.client.get_file(photo, filename)

    def deletePhoto(self, deleteList):
        for photo in deleteList:
            photoName=photo.split('/')[2]
            filename = 'images/'+photoName
            os.remove(filename)

    def rewriteDownloadedFile(self, sharedList):
        fp = open(Config['downloaded_file_txt'],'w')
        for photo in sharedList:
            fp.write(photo+'\n')
        fp.close()

    def run(self):
        while not self.stopped.wait(2):
            downloadedPhotos=[]
            sharedPhoto=[]
            fp = open(Config['downloaded_file_txt'],'r')
            for line in fp:
                downloadedPhotos.append(line.strip())
            fp.close()
            shared = self.client.get_shares("/", shared_with_me=True)
            photoPath = shared[0].share_info["path"]
            photos = self.client.list(photoPath)
            for photo in photos:
                sharedPhoto.append(photo.path)
            diff_download = list(set(sharedPhoto) - set(downloadedPhotos))
            if len(diff_download) > 0 :
                self.downloadPhoto(diff_download)
            diff_delete = list(set(downloadedPhotos) - set(sharedPhoto))
            if len(diff_delete) > 0:
                self.deletePhoto(diff_delete)
            if len(diff_download)>0 or len(diff_delete)>0:
                self.rewriteDownloadedFile(sharedPhoto)


if __name__ == '__main__':
    stopFlag = threading.Event()
    owncloudSyncThread = OwnCloudClient(stopFlag)
    owncloudSyncThread.daemon=True
    owncloudSyncThread.start()
    while owncloudSyncThread.is_alive:
        try:
            owncloudSyncThread.join(1)
        except KeyboardInterrupt:
            stopFlag.set()
            break
