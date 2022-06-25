import os
from datetime import datetime
import time
import hashlib
import requests


### Logger
class logger(object):

    def __init__(self):
        logs_dir = "./logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        self.logfile = logs_dir + os.path.sep + "httpcache.log"
        self.errorfile = self.logfile[:-4] + ".error.log"
        self.errorflag = self.logfile[:-4] + ".error.flag"

    def save(self, log):
        f = open(self.logfile, "a")
        text = str(datetime.now()) + ": " + log + "\r\n"
        f.write(text)
        f.close()

    def error(self, log):
        f = open(self.errorfile, "a")
        text = str(datetime.now()) + ": " + log + "\r\n"
        f.write(text)
        f.close()
        f = open(self.errorflag, "w")
        f.close()


### Shared Cache
class sharedcache(object):

    def __init__(self):
        self.cache_dir = "./cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def keys(self):
        keylist = []
        for filename in os.listdir(self.cache_dir):
            if filename[-4:].lower() == ".url":
                filename = self.cache_dir + os.path.sep + filename
                f = open(filename)
                content = f.readlines()
                f.close()
                if len(content) > 0:
                    keylist.append(content[0])
        return keylist

    #### asks for read
    def has_recent_access(self, key):
        namepreffix = hashlib.md5(key.encode("utf-8")).hexdigest()
        access_data = self._read_lastaccess_file(self.cache_dir + os.path.sep + namepreffix)
        if access_data["read"] is None:
            return False

        accesstime = time.strptime(access_data["read"], "%Y-%m-%d %H:%M")
        timestamp = time.mktime(accesstime)
        delta = datetime.now() - datetime.fromtimestamp(timestamp)
        if delta.days > 7:
            return False
        return True

    def convert_timedelta(self, duration):
        days, seconds = duration.days, duration.seconds
        hours = days * 24 + seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 60)
        return hours, minutes, seconds

    def must_be_updated(self, key):
        namepreffix = hashlib.md5(key.encode("utf-8")).hexdigest()
        access_data = self._read_lastaccess_file(self.cache_dir + os.path.sep + namepreffix)
        if access_data["write"] is None:
            return True

        accesstime = time.strptime(access_data["write"], "%Y-%m-%d %H:%M")
        timestamp = time.mktime(accesstime)
        delta = datetime.now() - datetime.fromtimestamp(timestamp)
        h, m, s = self.convert_timedelta(delta)
        if (h * 60 + m) > int(access_data["retry"]):
            return True
        return False

    def set_max_retry(self, key, minutes=15):
        namepreffix = hashlib.md5(key.encode("utf-8")).hexdigest()
        lastaccessname = self.cache_dir + os.path.sep + namepreffix
        self._save_lastaccess_file(lastaccessname, "retry", minutes)

    def clean(self, key):
        namepreffix = hashlib.md5(key.encode("utf-8")).hexdigest()
        for f in os.listdir(self.cache_dir):
            if f.startswith(namepreffix):
                f = self.cache_dir + os.path.sep + f
                os.remove(f)

    def remove_older(self, key):
        filename = None
        mtime = 0
        count = 0
        namepreffix = hashlib.md5(key.encode("utf-8")).hexdigest() + "."
        for f in os.listdir(self.cache_dir):
            if f.startswith(namepreffix) and f[-4:].lower() != ".url" and f[-11:].lower() != ".lastaccess":
                count += 1
                f = self.cache_dir + os.path.sep + f
                stats = os.stat(f)
                f_mtime = stats.st_mtime
                if stats.st_size > 0:
                    if mtime == 0:
                        mtime = f_mtime
                        filename = f
                    elif f_mtime < mtime:
                        mtime = f_mtime
                        filename = f
        if count > 2:
            os.remove(filename)

    def _print_all(self, key):
        filename = None
        namepreffix = hashlib.md5(key.encode("utf-8")).hexdigest() + "."
        mtime = 0
        for filename in os.listdir(self.cache_dir):
            if filename.startswith(namepreffix) and filename[-4:].lower() != ".url" and filename[-11:].lower() != ".lastaccess":
                content = ""
                filename = self.cache_dir + os.path.sep + filename
                f = open(filename)
                content = f.readlines()
                if len(content) == 1:
                    content = content[0]
                f.close()
                print(content)

    #### readfile
    def _read_lastaccess_file(self, lastaccessfile):
        access = {"read": None, "write": None, "retry": "15"}
        lastaccessfile = lastaccessfile + ".lastaccess"
        if not os.path.exists(lastaccessfile):
            return access
        f = open(lastaccessfile)
        content = f.readlines()
        f.close()
        for line in content:
            if line.startswith("read: "):
                access["read"] = line[6:].strip()
            if line.startswith("write: "):
                access["write"] = line[7:].strip()
            if line.startswith("retry: "):
                access["retry"] = line[7:].strip()
        return access

    #### savefile
    def _save_lastaccess_file(self, lastaccessfile, key, value):
        access_data = self._read_lastaccess_file(lastaccessfile)
        access_data[key] = value

        f = open(lastaccessfile + ".lastaccess", "w")
        if access_data["read"] is not None:
            f.write("read: " + access_data["read"] + "\r\n")
        if access_data["write"] is not None:
            f.write("write: " + access_data["write"] + "\r\n")
        if access_data["retry"] is not None:
            f.write("retry: " + str(access_data["retry"]) + "\r\n")
        f.close()

    def get(self, key):
        filename = None
        namepreffix = hashlib.md5(key.encode("utf-8")).hexdigest()
        mtime = 0
        for f in os.listdir(self.cache_dir):
            if f.startswith(namepreffix) and f[-4:].lower() != ".url" and f[-11:].lower() != ".lastaccess":
                f = self.cache_dir + os.path.sep + f
                stats = os.stat(f)
                f_mtime = stats.st_mtime
                if stats.st_size > 0 and f_mtime > mtime:
                    mtime = f_mtime
                    filename = f
        if filename is None:
            return None
        #### for read
        lastaccessname = self.cache_dir + os.path.sep + namepreffix
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._save_lastaccess_file(lastaccessname, "read", now)

        content = ""
        f = open(filename)
        content = f.readlines()
        if len(content) == 1:
            content = content[0]
        f.close()
        return content

    def save(self, key, value, save_read_access=True):
        filename = self.cache_dir + os.path.sep + hashlib.md5(key.encode("utf-8")).hexdigest()
        tmpfilename = self.cache_dir + os.path.sep + "tmp." + hashlib.md5(key.encode("utf-8")).hexdigest()
        ext = "." + hashlib.md5(str(time.time()).encode("utf-8")).hexdigest()
        if value:
            f = open(tmpfilename + ext, "w")
            self._write(f, value)
            f.close()
            os.rename(tmpfilename + ext, filename + ext)
        if not os.path.exists(filename + ".url"):
            f = open(filename + ".url", "w")
            f.write(key)
            f.close()
        #### for read/write
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._save_lastaccess_file(filename, "write", now)
        if save_read_access:
            self._save_lastaccess_file(filename, "read", now)

    def _write(self, f, value):
        if isinstance(value, str):
            f.write(value)
        elif isinstance(value, list):
            for elem in value:
                self._write(f, elem)
        else:
            raise Exception("HttpCache.SharedCache error: Only str or str lists allowed!")


### Producer
class producer(object):

    def __init__(self, cache, http_proxy=""):
        self.shared_cache = cache
        self.http_proxy_auth_string = http_proxy

    def _get_url_content(self, url):
        config = GLOBAL_CONFIG
        logger = config["logger"]
        content = None
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0'}
            response = requests.get(url, headers=headers)
            if response is None:
                logger.save("HttpCache.Producer: Warning: URL content is empty")
                content = None
            else:
                logger.save("HttpCache.Producer: Got URL content: " + url)
                content = response.content.decode("utf-8")
        except Exception as e:
            logger.save("HttpCache.Producer: Error getting URL content: " + str(e))
            content = None
        return content

    def produce(self, url, save_read_access=True):
        content = self._get_url_content(url)
        if content is not None and len(content) > 0:
            self.shared_cache.save(url, content, save_read_access)
        return content

    def clean_older(self, url):
        self.shared_cache.remove_older(url)

    def must_be_updated(self, url):
        return self.shared_cache.must_be_updated(url)

    def set_max_retry(self, url, minutes=15):
        self.shared_cache.set_max_retry(url, minutes)

    def has_recent_access(self, url):
        if not self.shared_cache.has_recent_access(url):
            self.shared_cache.clean(url)
            return False
        return True


### Consumer
class consumer(object):

    def __init__(self, cache, http_proxy=""):
        self.shared_cache = cache
        self.http_proxy_auth_string = http_proxy
        self.logger = logger

    def consume(self, url, save_cache=True):
        content = self.shared_cache.get(url)
        if not save_cache or content is None:
            p = producer(self.shared_cache, self.http_proxy_auth_string)
            content = p.produce(url)
        return content


### Global properties
GLOBAL_CONFIG = {
    "http_proxy": "",
    "shared_cache": sharedcache(),
    "logger": logger(),
}


### Public methods
def get_url_content(url, save_cache=True, config=GLOBAL_CONFIG):
    logger = config["logger"]
    logger.save("HttpCache.Client: Consumming url " + url)
    c = consumer(config["shared_cache"], config["http_proxy"])
    content = c.consume(url, save_cache)
    if content is None:
        logger.save("HttpCache.Client: ERROR. No content available for url " + url)
    return content


def set_url_retry_time(url, minutes, config=GLOBAL_CONFIG):
    logger = config["logger"]
    http_proxy = config["http_proxy"]
    shared_cache = config["shared_cache"]
    logger.save("HttpCache.RetryTime: Setting retry time on " + str(minutes) + " for url " + url)
    p = producer(shared_cache, http_proxy)
    p.set_max_retry(url, minutes)


def update_content(config=GLOBAL_CONFIG):
    shared_cache = config["shared_cache"]
    logger = config["logger"]
    http_proxy = config["http_proxy"]

    logger.save("== HttpCache.ProducerThread Update ==")
    for url in list(shared_cache.keys()):
        logger.save("HttpCache.ProducerThread: Producing url " + url)
        p = producer(shared_cache, http_proxy)
        if p.must_be_updated(url) and p.has_recent_access(url):
            content = p.produce(url, save_read_access=False)
            if content is None:
                logger.save("HttpCache.ProducerThread: ERROR. Could not produce content for url " + url)
                logger.error(url)
            logger.save("HttpCache.ProducerThread: Cleaning older entries for url " + url)
            p.clean_older(url)
        else:
            logger.save("HttpCache.ProducerThread: Cleaning ALL entries due to no recent access for url " + url)
    logger.save("== HttpCache.ProducerThread End Update ==")
