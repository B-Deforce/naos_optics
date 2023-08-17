import logging
from logging.handlers import TimedRotatingFileHandler
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def setup_logger(name: str, log_file: str = "../logs/app.log") -> logging.Logger:
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


def send_email(message, subject, from_email, to_email, api_key, logger):
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=message,
    )
    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        logger.info("Email sent!")
    except Exception as e:
        logger.info(f"Failed to send email: {e}")
