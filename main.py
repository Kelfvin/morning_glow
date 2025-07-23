import math
import re
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import schedule
import time
import logging
import yaml
from datetime import datetime
import random

from config import Config, SmtpConfig
import os
import sys

CONFIG_FILE = "config.yaml"
config = None


def load_config():

    global config
    config_dict = yaml.safe_load(open(CONFIG_FILE, "r", encoding="utf-8"))
    config = Config(config_dict)

    os.makedirs(os.path.dirname(config.log_path), exist_ok=True)
    logging.basicConfig(    
        filename=config.log_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.info("Configuration loaded successfully.")


def fetch_data() -> dict:
    url = "https://sunsetbot.top/"

    # query_id = Math.floor((Math.random()*10000000)+1).toString();
    query_id = str(math.floor((random.random()*10000000)+1))

    params = {
        "query_id": query_id,
        "intend": "select_city",
        "query_city": "四川省-成都",
        "event_date": None,
        "event": "set_1",
        "times": None,
        "model": "GFS"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        logging.error(f"Failed to fetch data. Status code: {response.status_code}")
        return
    data = response.json()
    return data





def send_email(content, to_addr, subject="观霞指数"):
    # 你的邮箱配置
    smtp_config:SmtpConfig = config.smtp

    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = Header(smtp_config.account)
    msg["To"] = Header(to_addr)
    msg["Subject"] = Header(subject, "utf-8")

    server = smtplib.SMTP_SSL(smtp_config.smtp_server, 465)
    server.login(smtp_config.account, smtp_config.password)
    server.sendmail(smtp_config.account, [to_addr], msg.as_string())
    server.quit()


def job():
    data = fetch_data()
    if not data:
        logging.error("No data fetched.")
        return

    def extract_value_and_desc(c):
        match = re.match(r"([\d\.]+)（(\S+)）", c)
        if match:
            value = match.group(1)
            desc = match.group(2)
            return value, desc

    # 判断逻辑
    tb_aod = data.get("tb_aod")  # 气溶胶指数
    tb_quality = data.get("tb_quality")  # 晚霞指数

    tb_aod_value, tb_aod_desc = extract_value_and_desc(
        tb_aod) if tb_aod else (None, None)
    tb_quality_value, tb_quality_desc = extract_value_and_desc(
        tb_quality) if tb_quality else (None, None)

    tb_aod_value = float(tb_aod_value) if tb_aod_value else None
    tb_quality_value = float(tb_quality_value) if tb_quality_value else None

    if tb_quality_value > config.quality_threshold:
        logging.info("晚霞指数较高，准备发送邮件...")
        logging.info(f"晚霞指数: {tb_quality_value} ({tb_quality_desc})")
        logging.info(f"气溶胶指数: {tb_aod_value} ({tb_aod_desc})")

        content = f"""# 今日晚霞指数较高！

        - 晚霞指数: {tb_quality_value} ({tb_quality_desc})
        - 气溶胶指数: {tb_aod_value} ({tb_aod_desc})
        """

        # 发送邮件
        email_list = config.email_list

        for addr in email_list:
            logging.info(f"Sending email to {addr}...")
            send_email(content, addr)
            logging.info(f"Email sent to {addr}.")

    else:
        logging.info("晚霞指数不高，今日无需发送邮件。")
        logging.info(f"晚霞指数: {tb_quality_value} ({tb_quality_desc})")
        logging.info(f"气溶胶指数: {tb_aod_value} ({tb_aod_desc})")


def main():
    load_config()
    logging.info(f"Configuration: {config}")
    
    # ---------------------------------------------------------------------------- #
    #                                   For Test                                   #
    # ---------------------------------------------------------------------------- #
    
    job()  # 直接执行一次任务，便于测试

    # 定时任务设置
    for send_time in config.send_time:
        try:
            datetime.strptime(send_time, "%H:%M")
            schedule.every().day.at(send_time).do(job)
            logging.info(f"定时任务设置成功: {send_time}")
        except ValueError:
            logging.error(f"无效的时间格式: {send_time}，请使用24小时制HH:MM格式，如08:00或23:59")

    logging.info("定时任务已启动...")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
