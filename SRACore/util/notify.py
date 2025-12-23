import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from plyer import notification

from SRACore.util import encryption
from SRACore.util.config import load_settings
from SRACore.util.logger import logger


def try_send_notification(title: str, message: str) -> bool:
    """尝试发送通知，返回是否成功"""
    setting = load_settings()
    if not setting.get('AllowNotifications', False):
        return False

    success = False
    if setting.get('AllowSystemNotifications', False):
        try:
            send_windows_notification(title, message)
            success = True
        except Exception as e:
            logger.error(f"系统通知发送失败: {e}")

    if setting.get('AllowEmailNotifications', False):
        try:
            if send_mail_notification(title, message, setting):
                success = True
            else:
                logger.warning("邮件通知配置不完整，请检查SMTP设置")
        except Exception as e:
            logger.error(f"邮件通知发送失败: {e}")

    return success


def test_notification() -> bool:
    """测试通知功能，发送欢迎消息"""
    setting = load_settings()

    # 检查通知是否启用
    if not setting.get('AllowNotifications', False):
        logger.warning("通知功能未启用，请先在设置中开启")
        return False

    # 检查是否至少启用了一种通知方式
    if not setting.get('AllowSystemNotifications', False) and not setting.get('AllowEmailNotifications', False):
        logger.warning("未启用任何通知方式，请在设置中启用系统通知或邮件通知")
        return False

    logger.info("开始测试通知...")
    success = try_send_notification("SRA", "欢迎使用SRA - 这是一条测试通知")

    if success:
        logger.info("测试通知发送成功")
    else:
        logger.warning("测试通知发送失败")

    return success


def send_windows_notification(title: str, message: str, timeout: int = 10):
    """
    发送 Windows 系统通知
    :param title: 通知标题
    :param message: 通知内容
    :param timeout: 通知显示时长（秒）
    """

    # 发送通知
    notification.notify(title=title, message=message, app_name="SRA", timeout=timeout)


def send_mail_notification(title: str = "SRA", message: str = "", config: dict | None = None) -> bool:
    """发送邮件通知，返回是否成功"""
    config = config or {}
    SMTP = config.get("SmtpServer", "")
    port = config.get("SmtpPort", 465)
    sender = config.get("EmailSender", "")
    auth_code = config.get("EmailAuthCode", "")
    password = encryption.win_decryptor(auth_code) if auth_code else ""
    receiver = config.get("EmailReceiver", "")
    return send_mail(title, "SRA通知", message, SMTP, port, sender, password, receiver)


def send_mail(
        title: str = "SRA",
        subject: str = "SRA通知",
        message: str = "",
        SMTP: str = "",
        port: int = 465,
        sender: str = "",
        password: str = "",
        receiver: str = "",
) -> bool:
    """发送邮件"""
    if SMTP == "" or sender == "" or password == "" or receiver == "":
        return False
    try:
        msg = MIMEText(message, 'plain', 'utf-8')
        msg['From'] = formataddr((title, sender))
        msg['To'] = formataddr(("User", receiver))
        msg['Subject'] = subject

        server = smtplib.SMTP_SSL(SMTP, port)
        server.login(sender, password)
        server.sendmail(sender, [receiver, ], msg.as_string())
        server.quit()
        return True
    except Exception:
        raise


class Summary:
    def __init__(self):
        self.date = None
        self.time = 0
        self.success = 0
        self.failed = 0
        self.skipped = 0
        self.total = 0
        self.config = []
        self.warning: list[tuple] = []
        self.error: list[tuple] = []
        self.additional_info: list[tuple] = []

    def __str__(self) -> str:
        warning_str = ""
        for i in self.warning:
            warning_str += f"来源 {i[0]} 信息: {i[1]}\n"
        error_str = ""
        for i in self.error:
            error_str += f"来源 {i[0]} 信息: {i[1]}\n"
        additional_info_str = ""
        for i in self.additional_info:
            additional_info_str += f"来源 {i[0]} 信息: {i[1]}\n"
        mes = f"您好！您在 {self.date} 启动的任务已经完成！\n" \
              f"本次任务的结果如下：\n" \
              f"成功：{self.success}，失败：{self.failed}，跳过：{self.skipped}，总：{self.total}, 耗时：{self.time}秒\n" \
              f"收到警告：{len(self.warning)}, 遇到错误：{len(self.error)}\n" \
              f"细节: \n" \
              f"警告: \n{warning_str}\n" \
              f"错误: \n{error_str}\n" \
              f"附加信息: \n{additional_info_str}\n" \
              f"感谢您的使用！--SRA\n"
        return mes
