"""Exceptions for the MQTT client."""

class MqttClientError(Exception):
    """Exception to indicate a general error."""


class MqttClientCommunicationError(
    MqttClientError
):
    """Exception to indicate a communication error."""


class MqttClientAuthenticationError(
    MqttClientError
):
    """Exception to indicate an authentication error."""
