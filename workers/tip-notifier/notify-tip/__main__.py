import os
from typing import Dict
import requests
import logging
from time import sleep

def get_relay_block_num(ekg_hostname: str, ekg_port: int):
    url = f"http://{ekg_hostname}:{ekg_port}/"
    res = requests.get(url, headers={"Accept": "application/json"})
    data = res.json()
    logging.debug(data)
    return data["cardano"]["node"]["metrics"]["blockNum"]["int"]["val"]


def notify_node_block_num(hostname: str, port: int, valency: int, block_num: int, network_magic: int):
    url = f"https://api.clio.one/htopology/v1/?port={port}&blockNo={block_num}&valency={valency}&magic={network_magic}&hostname={hostname}"
    res = requests.get(url, headers={"Accept": "application/json", "X-Forwarded-For": "54.218.63.142"})
    data = res.json()
    logging.debug(data)
    return data


def notify_tip(
    network_magic: int,
    ekg_hostname: str,
    ekg_port: str,
    relay_public_hostname: str,
    relay_public_port: int,
    relay_valency: int,
) -> Dict[str, None]:
    logging.debug("retrieving latest block from node")

    block_num = get_relay_block_num(
        ekg_hostname=ekg_hostname,
        ekg_port=ekg_port,
    )

    logging.info(f"found current block number for node {block_num}")

    logging.debug("notifying latest block to external api")

    notify_node_block_num(
        hostname=relay_public_hostname,
        port=relay_public_port,
        valency=relay_valency,
        block_num=block_num,
        network_magic=network_magic,
    )


def load_env_var(key: str, default: str = None) -> str:
    value = os.environ.get(key, default)

    if not value:
        raise Exception(f"Required env var [{key}] is not present")

    return value

def load_int_env_var(key: str, default: int = None) -> int:
    raw = load_env_var(key, str(default))
    return int(raw)

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)

while True:
    try:
        notify_tip(
            network_magic=load_int_env_var("NETWORK_MAGIC"),
            ekg_hostname=load_env_var("EKG_HOSTNAME", "localhost"),
            ekg_port=load_int_env_var("EKG_PORT"),
            relay_public_hostname=load_env_var("RELAY_PUBLIC_HOSTNAME"),
            relay_public_port=load_int_env_var("RELAY_PUBLIC_PORT"),
            relay_valency=load_int_env_var("RELAY_VALENCY", 1),
        )
    except Exception as err:
        logging.error(err)

    logging.debug("sleeping for a while")
    sleep(60*60)
