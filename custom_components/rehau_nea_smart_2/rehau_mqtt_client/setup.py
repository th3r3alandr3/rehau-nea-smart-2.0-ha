"""Set up the Rehau MQTT client."""
from setuptools import setup, find_packages

setup(
    name='rehau_mqtt_client',
    version='0.2',
    packages=find_packages(),
    install_requires=[
        'asyncio==3.4.3',
        'certifi==2023.11.17',
        'charset-normalizer==3.3.2',
        'future==0.18.3',
        'idna==3.6',
        'lz4==4.3.3',
        'paho-mqtt==1.6.1',
        'requests==2.31.0',
        'urllib3==1.26.18',
        'httpx==0.27.0',
        'pydantic==2.6.3',
        'apscheduler==3.9.1',
        'deepmerge==1.1.1',
        'schedule==1.2.1',
    ],
)
