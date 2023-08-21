import logging
from logging.handlers import TimedRotatingFileHandler
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)
import base64


def setup_logger(name: str, log_file: str = "logs/app.log") -> logging.Logger:
    """
    Set up a logger with the given name, and return the logger.
    The logger is set up to create a new log file every day, and to keep 7 days of logs.
    :param name: The name of the logger.
    :return: The logger.
    """
    # Create a logger
    logger = logging.getLogger(name)

    # Set the log level
    logger.setLevel(logging.INFO)

    # Create a handler that creates a new log file every day and keeps 7 days of logs
    handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=7
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    # Add the handler to the logger
    logger.addHandler(handler)

    return logger


# goggles SKU is too long as it exists of 3 parts, hence we replcae the frame sku with the goggle name
# however, since the stock system is built on SKU, we create a mapping from frame name to SKU
# this is public information, so no need to hide it
sku_replace = {"SELVA": "6095936367383", "VIRTAUS": "6095930196101"}

# maps sku of frame to sku of corresponding clear lens
sku_frames_to_clear = {
    '6095936367383': '6095946877810',  # STOCK-TRACKING: SELVA FRAME
    '6095930196101': '6095935353387',  # STOCK-TRACKING: VIRTAUS FRAME
    '6095926198102': '6095950193135',  # STOCK-TRACKING: VUORI FRAME|Glossy White
    '6095927077093': '6095950193135',  # STOCK-TRACKING: VUORI FRAME|Matte Black
    '6095930865847': '6095950193135',  # STOCK-TRACKING: VUORI FRAME|Matte Black OLD
    '6095939782718': '6095950193135',  # STOCK-TRACKING: VUORI FRAME|Matte Blue
    '6095930631626': '6095950193135',  # STOCK-TRACKING: VUORI FRAME|Matte Desert
    '6095926186161': '6095950193135',  # STOCK-TRACKING: VUORI FRAME|Matte Green
    '6095927234274': '6095950193135',  # STOCK-TRACKING: VUORI FRAME|Matte Pink
}


def send_email(message, subject, from_email, to_email, api_key, logger=None, attachment=None, filetype=None):
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=message,
    )
    if attachment:
        with open(attachment, 'rb') as f:
            data = f.read()
            f.close()
        encoded_file = base64.b64encode(data).decode()

        attachedFile = Attachment(
            FileContent(encoded_file),
            FileName(attachment),
            FileType(filetype),
            Disposition('attachment')
        )
        message.attachment = attachedFile

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        if logger:
            logger.info("Email sent!")
    except Exception as e:
        if logger:
            logger.info(f"Failed to send email: {e}")
