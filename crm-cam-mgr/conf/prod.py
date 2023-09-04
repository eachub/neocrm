URL_PREFIX = "/neocrm/api/cam/mgr"

KAFKA_METADATA_SECONDS = 30  # max_age
KAFKA_API_VERSION = "auto"  # "0.9.1"
KAFKA_BOOTSTRAP_SERVERS = ["127.0.0.1:9092", ]
KAFKA_CONSUMER_GID = ""
KAFKA_TOPIC = ["t_web_traffic_event", "t_wmp_share_event"]

PEOPLE_FILE_DIR="/opt/nfs/neocrm/cam"