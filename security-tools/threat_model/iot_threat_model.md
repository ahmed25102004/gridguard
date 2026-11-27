# GridGuard IoT and MQTT Threat Model

## 1. Document Purpose

This document identifies and analyzes security threats affecting the
GridGuard IoT communication baseline.

The scope focuses on MQTT communication between smart-grid edge devices
and the EMQX MQTT broker, including the broker deployment environment.

This is a baseline threat model for Sprint 1 – Lane 7:
IoT and Communication Security.

## 2. System Context

GridGuard is an AI-powered smart-grid cybersecurity and monitoring platform.

The repository currently contains:
- A backend API.
- An AI/ML anomaly detection service.
- An IoT firmware directory intended for edge-device firmware.
- An IoT simulator directory intended for simulated telemetry.
- A deployments directory.
- A security-tools directory.

The firmware and simulator directories currently contain README files
rather than implemented MQTT clients.

Therefore, the MQTT communication flow below represents the target
architecture for this task, not an already implemented integration.

### 2.1 Target Communication Flow

1. Smart-grid edge devices generate telemetry.
2. Devices publish telemetry messages using MQTT.
3. The EMQX broker receives and manages MQTT messages.
4. Authorized GridGuard consumers may subscribe to telemetry topics.

The integration between EMQX and the backend or AI service must be
implemented or verified separately.

### 2.2 MQTT Topic Namespace

The proposed topic structure is:

grid/substations/{sub_id}/feeders/{feeder_id}/assets/{asset_id}/telemetry

Where:
- sub_id identifies a substation.
- feeder_id identifies a feeder within a substation.
- asset_id identifies an asset or edge device.
- telemetry represents measurement data.

The backend currently defines a Substation model with an integer ID.
Feeder and asset identifiers are part of the proposed MQTT namespace;
their corresponding backend models have not been confirmed.

## 3. Assets to Protect

| Asset | Security Importance |
|---|---|
| MQTT broker | Controls message exchange |
| Telemetry messages | Must remain accurate and trustworthy |
| Device identity | Prevents unauthorized device impersonation |
| MQTT topics | Organize access to telemetry data |
| Broker configuration | Controls network exposure and connection behavior |
| Docker network | Limits access to the broker |
| Operational availability | Supports continuous monitoring |

## 4. Trust Boundaries

The threat model considers the following trust boundaries:

1. Edge devices to MQTT broker:
   Messages originate from devices outside the broker container.

2. Docker host to broker network:
   Host port publishing can expose broker listeners beyond the intended
   internal network if configured incorrectly.

3. MQTT broker to downstream consumers:
   Consumers must receive data through an explicitly configured integration.

4. Administrative access to broker:
   Broker management interfaces must not be exposed unnecessarily.

## 5. STRIDE Threat Analysis

### 5.1 Spoofing

**Threat:** An attacker impersonates a legitimate IoT device and connects
to the MQTT broker.

**Affected assets:** Device identity and telemetry integrity.

**Example scenario:** An unauthorized MQTT client publishes fake sensor
readings using a legitimate-looking device topic.

**Potential impact:**
- False telemetry.
- Incorrect monitoring results.
- Misleading operational decisions.

**Baseline mitigations:**
- Disable anonymous MQTT connections.
- Require configured client authentication.
- Restrict broker access to the intended Docker network.
- Avoid exposing MQTT listeners publicly.

**Future security improvements:**
- Mutual TLS (mTLS).
- Unique device certificates.
- Strong device identity management.

### 5.2 Tampering

**Threat:** An attacker modifies, injects, or replaces telemetry messages.

**Affected assets:** Telemetry accuracy and downstream monitoring.

**Example scenario:** A malicious client publishes manipulated voltage
or current measurements to a telemetry topic.

**Potential impact:**
- Incorrect anomaly detection.
- False alerts.
- Misleading grid monitoring information.

**Baseline mitigations:**
- Disable anonymous connections.
- Restrict access to the broker.
- Use a consistent topic namespace.
- Validate telemetry payloads in downstream consumers.

**Future security improvements:**
- TLS-protected MQTT communication.
- Message integrity validation.
- Topic-level authorization policies.

### 5.3 Repudiation

**Threat:** A client denies publishing a message or performing an MQTT
operation.

**Affected assets:** Auditability and incident investigation.

**Example scenario:** A device operator denies that a telemetry message
was published by their device.

**Potential impact:**
- Difficulty investigating incidents.
- Reduced accountability.
- Incomplete security records.

**Baseline mitigations:**
- Enable appropriate broker logging.
- Record relevant connection and disconnection events.
- Preserve available timestamps and client identifiers.

**Future security improvements:**
- Centralized audit logging.
- Protected log storage.
- Device-level identity and event correlation.

### 5.4 Information Disclosure

**Threat:** An unauthorized party accesses telemetry data or broker
management information.

**Affected assets:** Telemetry confidentiality and infrastructure details.

**Example scenario:** An attacker reaches an exposed MQTT listener and
attempts to subscribe to telemetry topics.

**Potential impact:**
- Exposure of operational measurements.
- Disclosure of infrastructure information.
- Increased opportunities for further attacks.

**Baseline mitigations:**
- Keep the broker on an isolated Docker bridge network.
- Do not publish the unencrypted MQTT port (1883) to external interfaces.
- Avoid exposing management listeners unnecessarily.
- Disable anonymous connections.

**Future security improvements:**
- TLS 1.3.
- Mutual TLS.
- Topic-level read authorization.

### 5.5 Denial of Service

**Threat:** An attacker overwhelms the broker with excessive connections
or messages.

**Affected assets:** Broker availability and telemetry delivery.

**Example scenario:** A client opens excessive MQTT connections or
publishes messages at an abnormal rate.

**Potential impact:**
- Increased resource consumption.
- Delayed telemetry delivery.
- Broker service interruption.

**Baseline mitigations:**
- Configure appropriate listener connection limits.
- Apply broker resource limits where supported.
- Restrict network access to the broker.
- Test connection timeout behavior.

**Future security improvements:**
- Per-client message rate limits.
- Monitoring and alerting.
- Additional network-level denial-of-service protections.

### 5.6 Elevation of Privilege

**Threat:** An MQTT client gains permissions beyond its intended role.

**Affected assets:** MQTT topics and telemetry operations.

**Example scenario:** A telemetry publisher attempts to access topics
or perform operations intended for another device or administrative client.

**Potential impact:**
- Unauthorized publication.
- Unauthorized subscription.
- Manipulation or exposure of telemetry.

**Baseline mitigations:**
- Disable anonymous connections.
- Define the expected client authentication configuration.
- Keep administrative interfaces restricted.
- Document the intended topic ownership and access boundaries.

**Future security improvements:**
- Topic-level publish and subscribe ACLs.
- Least-privilege device identities.
- Separate administrative and device accounts.

## 6. Baseline Security Requirements

The following requirements apply to this task:

1. The EMQX broker must run in Docker.
2. The broker must use an isolated Docker bridge network.
3. Anonymous MQTT connections must be disabled.
4. Listener connection limits must be configured.
5. The unencrypted MQTT port 1883 must not be exposed externally.
6. Sensitive configuration values must be supplied through environment
   variables rather than hardcoded credentials.
7. MQTT topic naming must follow the documented namespace.
8. Security tests must verify network exposure and connection timeout
   behavior.

## 7. Scope and Limitations

This task establishes a baseline MQTT deployment and security configuration.

The following capabilities are considered future improvements unless
explicitly required by a later task:
- TLS 1.3 and mutual TLS.
- X.509 device certificates.
- Advanced topic-level ACL policies.
- Full device provisioning and lifecycle management.
- Production integration between EMQX and the backend.

The current repository does not yet contain implemented MQTT firmware
or simulator clients. Integration behavior must therefore be verified
when those components are implemented.

## 8. Conclusion

The STRIDE analysis identifies risks involving device impersonation,
telemetry manipulation, repudiation, information disclosure, denial of
service, and privilege escalation.

The baseline deployment aims to reduce these risks through broker
hardening, network isolation, restricted listener exposure, disabled
anonymous access, and security testing.

Additional controls such as mutual TLS and topic-level authorization
can strengthen the system in subsequent development tasks.
