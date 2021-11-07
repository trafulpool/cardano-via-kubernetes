import os
from typing import Any, Dict
import requests
import logging
import json
from kubernetes import client, config


def get_relay_block_num(ekg_hostname: str, ekg_port: int):
    url = f"http://{ekg_hostname}:{ekg_port}/"
    res = requests.get(url, headers={"Accept": "application/json"})
    data = res.json()
    logging.debug(data)
    return data["cardano"]["node"]["metrics"]["blockNum"]["int"]["val"]


def fetch_latest_topology(max_peers: int, network_magic: int):
    url = f"https://api.clio.one/htopology/v1/fetch/?max={max_peers}&magic={network_magic}&ipv=4"
    res = requests.get(url, headers={"Accept": "application/json"})
    data = res.json()
    logging.debug(data)
    return {"Producers":  data["Producers"]}


def parse_string_peer(raw: str) -> Dict[str, Any]:
    parts = raw.split(",")

    return {
        "addr": parts[0],
        "port": int(parts[1]),
        "valency": int(parts[2]),
    }


def parse_string_topology(raw: str) -> Dict[str, Any]:
    peers = raw.split("|")

    return {
        "Producers": [parse_string_peer(peer) for peer in peers]
    }


def merge_topologies(topology_a: Dict[str, Any], topology_b: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Producers": [
            *topology_a["Producers"],
            *topology_b["Producers"],
        ]
    }


def replace_config_map(name: str, namespace: str, topology: Dict[str, Any]):
    config.load_incluster_config()
    v1 = client.CoreV1Api()

    cmap = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name=name),
        data={"topology.json": json.dumps(topology)}
    )

    v1.replace_namespaced_config_map(
        name=name,
        namespace=namespace,
        body=cmap
    )


def update_toplogy(
    network_magic: int,
    custom_topology_string: str,
    cmap_name: str,
    cmap_namespace: str,
    max_external_peers: int,
) -> Dict[str, None]:
    logging.debug("fetching latest topology from external api")

    external_topology = fetch_latest_topology(
        max_peers=max_external_peers,
        network_magic=network_magic,
    )

    logging.info("received external topology")

    logging.debug("parsing custom peers")

    custom_topology = parse_string_topology(
        raw=custom_topology_string
    )

    logging.debug("merging external topology and custom peers")

    merged = merge_topologies(external_topology, custom_topology)

    logging.debug("replacing k8s config map")

    replace_config_map(cmap_name, cmap_namespace, merged)

    logging.info("configmap replaced")


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

update_toplogy(
    network_magic=load_int_env_var("NETWORK_MAGIC"),
    custom_topology_string=load_env_var("CUSTOM_TOPOLOGY_STRING", ""),
    max_external_peers=load_int_env_var("MAX_EXTERNAL_PEERS", 15),
    cmap_name=load_env_var("CMAP_NAME", "relay-topology"),
    cmap_namespace=load_env_var("CMAP_NAMESPACE", "default"),
)
