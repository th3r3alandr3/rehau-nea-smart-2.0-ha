"""Enums for the Rehau NEA Smart 2 MQTT integration."""
from enum import Enum

class OperationModes(Enum):
    """Operation modes."""
    UNKNOWN = -1
    HEATING_ONLY = 1
    COOLING_ONLY = 2
    AUTO = 3
    HEATING_MANUAL = 5
    COOLING_MANUAL = 6


class EnergyLevels(Enum):
    """Energy levels."""

    PRESENT_MODE = 0
    ABSENT_MODE = 1
    STANDBY_MODE = 2
    TIMING_MODE = 3
    PARTY_MODE = 7
    HOLIDAY_MODE = 11


class ServerTopics(Enum):
    """Server topics."""

    USER_AUTH = "server/user/auth"
    USER_CREATE = "server/user/create"
    USER_READ = "server/{id}/v1/install/user/read"
    LAST_VERSION_READ = "server/{id}/v1/install/version/read/last"
    UPDATE_VERSION = "server/{id}/v1/install/version/update"
    USER_LOGOUT = "server/user/logout"
    USER_REFRESH_TOKEN = "server/user/refreshToken"
    USER_REFERENTIAL = "server/{email}/v1/install/user/referential"
    USER_ASK_STATISTICS = "server/{email}/{id}/v1/install/statistic/read"
    ASSOCIATE_CREATE = "server/{id}/v1/install/associate/create"
    ASSOCIATE_DELETE = "server/{id}/v1/install/associate/delete"
    UPDATE_ADMIN = "server/{id}/v1/install/updateadmin"
    ASSOCIATE_DELETE_FOR_USER = "server/{email}/{id}/v1/install/associate/user/delete"
    ASSOCIATE_CREATE_FOR_USER = "server/{email}/{id}/v1/install/associate/user/create"
    USER_UPDATE = "server/{id}/v1/install/user/update"
    GEOFENCING_UPDATE = "server/{email}/{id}/v1/install/geofencing/user/update"
    INSTALL_UPDATE = "server/{id}/v1/install/amend"
    INSTALL_ABSENCE_ACTIVATE = "server/{email}/{id}/v1/install/absence/active"
    INSTALL_ABSENCE_DEACTIVATE = "server/{email}/{id}/v1/install/absence/deactive"
    GROUP_UPDATE = "server/{id}/v1/install/zonegroup/update"
    GROUP_DELETE = "server/{id}/v1/install/zonegroup/delete"
    GROUP_CREATE = "server/{id}/v1/install/zonegroup/create"
    ZONE_UPDATE = "server/{id}/v1/install/zone/update"
    PROGRAM_NAME = "server/{email}/{id}/v1/install/program/name"
    ROOM_PROGRAM_SET = "server/{email}/{id}/v1/install/zone/program/set"
    ROOM_PROGRAM_UNSET = "server/{email}/{id}/v1/install/zone/program/unset"
    SEND_EMAIL_REPORT = "server/{email}/{id}/v1/install/flowtemperature/sendReport"
    ERROR_SEARCH = "server/{email}/{id}/v1/install/error/search"
    MIXED_CIRCUITS_SEARCH = "server/{email}/{id}/v1/install/mixedcircuit/search"
    ERROR_SETTINGS = "server/{email}/{id}/v1/install/error/settings"
    SEND_ERROR_MESSAGES_EMAIL = "server/{email}/{id}/v1/install/error/sendReport"
    SEND_WEATHER_TO_CC = "server/{id}/v1/install/weather"
    UPDATE_OWNER = "server/{id}/v1/install/installer/updateowner"
    UPDATE_TIME_ZONE = "server/{id}/v1/install/updatetimezone"


class ClientTopics(Enum):
    """Client topics."""

    BASE = "client/"
    LISTEN = "client/{email}"
    LISTEN_TO_CONTROLLER = "client/{id}/realtime"
    INSTALLATION = "client/{id}"
