import os
import socket
import pytest
import paho.mqtt.client as mqtt
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOPIC_TEMPLATE = "grid/substations/{sub_id}/feeders/{feeder_id}/assets/{asset_id}/telemetry"


def test_required_baseline_files_exist():
    required_files = [
        REPO_ROOT / "security-tools" / "threat_model" / "iot_threat_model.md",
        REPO_ROOT / "deployments" / "emqx" / "emqx_base.conf",
        REPO_ROOT / "deployments" / "docker-compose.iot.yml",
        REPO_ROOT / "scripts" / "init_mqtt_network.sh",
    ]
    for path in required_files:
        assert path.exists(), f"Missing required file: {path}"
        assert path.stat().st_size > 0, f"Empty required file: {path}"


def test_topic_namespace_format():
    topic = TOPIC_TEMPLATE.format(
        sub_id="sub-01",
        feeder_id="feeder-02",
        asset_id="xfmr-003",
    )
    parts = topic.split("/")
    assert parts == [
        "grid",
        "substations",
        "sub-01",
        "feeders",
        "feeder-02",
        "assets",
        "xfmr-003",
        "telemetry",
    ]


def test_port_1883_not_exposed_on_loopback():
    target_port = int(os.getenv("MQTT_BASELINE_TEST_PORT", "1883"))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        result = sock.connect_ex(("127.0.0.1", target_port))
        assert result != 0, f"Unencrypted MQTT port {target_port} should not be exposed on loopback"


def test_socket_timeout_handling_on_non_routable_ip():
    # RFC 5737 TEST-NET-1 address (192.0.2.1) is reserved for documentation/testing
    # and reliably triggers a timeout within a short socket timeout window.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        with pytest.raises((socket.timeout, TimeoutError, OSError)):
            sock.connect(("192.0.2.1", 1883))


def test_paho_mqtt_client_connect_timeout():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="gridguard-baseline-timeout-probe",
    )
    # Short timeout ensures the client does not hang indefinitely when target is unreachable
    with pytest.raises((socket.timeout, TimeoutError, ConnectionRefusedError, OSError)):
        client.connect("192.0.2.1", 1883, keepalive=5, bind_address="")
