# %%
import json
from pathlib import Path
import brotli
import time
import re
import requests, urllib
import logging, warnings
import sys
import socket, socks
# %%
BASIC_HEADER = {
    "accept":
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
    "dnt": "1",
    "accept-encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive"
}
# %% logging setting and file path
warnings.filterwarnings('ignore')
root_path = Path().resolve()
log_file = root_path / 'checkin.log'
fh = logging.FileHandler(encoding='utf-8', mode='a', filename=log_file)
logging.basicConfig(handlers=[fh],
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')

if sys.version_info.major == 2:
    logging.getLogger("requests").setLevel(logging.WARNING)

config_file = root_path / 'config.json'


# %%
def config_load(file):
    if not file.exists():
        return
    return json.load(open(file))


# %%
class DiscuzCheckin():

    def __init__(self, task, ft_key):
        #构建基本配置
        self.ft_key = ft_key
        #构建任务信息
        self.domain = task['domain'].strip()
        if not task['checkin_url'] or task['checkin_url'] == "":
            task["checkin_url"] = task["domain"] + "/plugin.php"
        self.extracted_domain = self.extract_domain(self.domain)
        self.url = task['checkin_url'] + '?' if not '?' in task[
            'checkin_url'] else task['checkin_url']
        self.is_proxy = task['proxy']
        self.method = task['method']
        if "query_string_parameters" in task['param']:
            self.query_string_parameters = task['param'][
                'query_string_parameters']
            self.query_string_parameters = urllib.parse.urlencode(
                self.query_string_parameters, safe=':')
            self.url += self.query_string_parameters
        if "form_data" in task['param']:
            self.form_data = task['param']['form_data']
        self.header = BASIC_HEADER
        self.header.update({
            "cookies": task['param']['cookies'],
            "origin": self.domain,
        })
        self.cookies = {}
        for x in task['param']['cookies'].split(";"):
            k, v = x.split("=")
            self.cookies.update({k.strip(): v.strip()})

        assert self.method in ['get', 'post'], "HTTP Method ERROR."

        #构建函数跳转表，处理签到结果
        self.result_jump_table = {
            "已签|已经签到|签过到": self.has_checked,
            "签到成功|奖励": self.success,
            "未定义|非法": self.cookie_err,
        }

    def send_ft(self, text):
        try:
            ft_url = f"https://sctapi.ftqq.com/{self.ft_key}.send?title={text}"
            requests.get(ft_url)
            return True
        except:
            return False

    def has_checked(self):
        logging.info("已经签到 URL: {}".format(self.extracted_domain))
        print("已签{}".format(self.extracted_domain))
        return

    def success(self):
        logging.info("签到成功 URL: {}".format(self.extracted_domain))
        print("成功{}".format(self.extracted_domain))
        return

    def cookie_err(self):
        logging.error("签到失败 URL: {}, cookies或formhash过期".format(
            self.extracted_domain))
        print("非法失败{}".format(self.extracted_domain))
        text = f"{self.extracted_domain}, 签到出现非法失败, 手动更新cookies或formhash"
        self.send_ft(text)
        return

    def failed(self):
        logging.error("签到失败 URL: {}, 未知错误".format(self.extracted_domain))
        print("未知失败{}".format(self.extracted_domain))
        text = f"{self.extracted_domain}, 签到出现未知失败"
        self.send_ft(text)
        return

    def get_randint(self, min_num, max_num):
        if min_num > max_num:
            raise ValueError("Illegal arguments...")
        return random.randint(min_num, max_num)

    def extract_domain(self, url):
        if not url:
            return ""

        start = url.find("//")
        if start == -1:
            start = -2

        end = url.find("/", start + 2)
        if end == -1:
            end = len(url)

        return url[start + 2:end]

    def checkin(self, retry=0):
        # proxies = PROXY if self.is_proxy else None
        if self.is_proxy:
            socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 12450)
            socket.socket = socks.socksocket
        try:
            if self.method == 'get':
                self.response = requests.get(self.url,
                                             headers=self.header,
                                             cookies=self.cookies)
            else:
                self.response = requests.post(self.url,
                                              headers=self.header,
                                              cookies=self.cookies,
                                              data=self.form_data)

            # print("+++++++++++++++++++++++++++")
            # print(response.text)
            if self.response.status_code == 200:
                for key in self.result_jump_table:
                    if re.findall(key, self.response.text) != []:
                        self.result_jump_table[key]()
                        break
                else:
                    self.failed()
                    retry -= 1
                    if retry > 0:
                        time.sleep(get_randint(30, 60))
                        self.checkin()
                self.response.close()
                return
            else:
                print(self.response.status_code)

        except requests.RequestException as e:
            logging.error(str(e))
            retry -= 1

            if retry > 0:
                time.sleep(self.get_randint(30, 60))
                self.checkin()

            self.failed()
        finally:
            time.sleep(3)


# %%
if __name__ == "__main__":
    config = config_load(config_file)
    assert config is not None, "Config file EMPTY."
    assert "domains" in config and config['domains'], "Domains EMPTY."

    if "retry" in config and config["retry"] > 0:
        RETRY_NUM = int(config["retry"])

    if "proxyServer" in config and type(config["proxyServer"]) == dict:
        PROXY = config["proxyServer"]

    # sleep
    if "waitTime" in config and 0 < config["waitTime"] <= 24:
        time.sleep(get_randint(0, config["waitTime"] * 60 * 60))

    tasks = config["domains"]
    for task in tasks:
        dz = DiscuzCheckin(task, config['ft_key'])
        dz.checkin(retry=0)
# %%
