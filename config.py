from datetime import datetime
import logging


class Config:
    def __init__(self, config:dict) -> None:
        self.smtp = SmtpConfig.from_dict(config.get("smtp", {}))
        self.email_list = config.get("email_list", [])

        self.send_time = []
        for send_time in config.get("send_time", []):
            try:
                datetime.strptime(send_time, "%H:%M")
                self.send_time.append(send_time)
            except ValueError:
                logging.error(f"无效的时间格式: {send_time}，请使用24小时制HH:MM格式，如08:00或23:59")

        self.quality_threshold = float(config.get("quality_threshold", 0.5))

        self.query_city = config.get("query_city", "四川省-成都")

        self.log_path = config.get("log_path", "logs/morning_glow.log")



class SmtpConfig:
    def __init__(self, smtp_server, account, password):
        self.smtp_server = smtp_server
        self.account = account
        self.password = password

    def __str__(self):
        return f"SmtpConfig(smtp_server={self.smtp_server}, account={self.account})"

    @staticmethod
    def from_dict(config_dict) -> "SmtpConfig":
        return SmtpConfig(
            smtp_server=config_dict.get("smtp_server"),
            account=config_dict.get("account"),
            password=config_dict.get("password")
        )