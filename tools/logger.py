import logging

logging.basicConfig(
    filename="platform.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def log(msg):
    logging.info(msg)
