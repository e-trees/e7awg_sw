import os
import pwd
import stat
import fcntl
import threading
import time

class ReentrantFileLock(object):
    """スレッド間, プロセス間排他可能なファイルロック"""

    def __init__(self, filepath):
        dirname = os.path.dirname(filepath)
        os.makedirs(dirname, exist_ok = True)        
        dir_owner = os.stat(dirname).st_uid
        if dir_owner == os.getuid():
            os.chmod(dirname, 0o777)
        self.__lock_fp = self.__get_fp(filepath)
        file_owner = os.stat(filepath).st_uid
        if file_owner == os.getuid():
            s = stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH
            os.chmod(filepath, s)

        self.__num_holds = 0
        self.__rlock = threading.RLock()


    def __get_fp(self, filepath):
        for i in range(80):
            try:
                return open(filepath, 'w')
            except:
                time.sleep(0.1)

        raise TimeoutError('[ReentrantFileLock]  open file timeout')


    def acquire(self):
        self.__rlock.acquire()
        self.__num_holds += 1
        fcntl.flock(self.__lock_fp.fileno(), fcntl.LOCK_EX)


    def release(self):
        self.__num_holds -= 1
        if self.__num_holds == 0:
            fcntl.flock(self.__lock_fp.fileno(), fcntl.LOCK_UN)
        self.__rlock.release()


    def discard(self):
        self.__lock_fp.close()
    
    
    def __enter__(self):
        self.acquire()


    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
