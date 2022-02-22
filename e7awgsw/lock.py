import os
import fcntl
import threading

class ReentrantFileLock(object):
    """スレッド間, プロセス間排他可能なファイルロック"""

    def __init__(self, filepath):
        dirname = os.path.dirname(filepath)
        os.makedirs(dirname, exist_ok = True)
        self.__lock_fp = open(filepath, 'w')
        self.__num_holds = 0
        self.__rlock = threading.RLock()


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
