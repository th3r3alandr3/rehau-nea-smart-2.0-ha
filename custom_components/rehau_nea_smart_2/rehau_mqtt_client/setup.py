"""Set up the Rehau MQTT client."""
from setuptools import setup, find_packages

setup(
    name='rehau_mqtt_client',
    version='0.4.9',
    packages=find_packages(),
    install_requires=[
        'asyncio==3.4.3',
        'certifi==2023.11.17',
        'charset-normalizer==3.3.2',
        'future==0.18.3',
        'idna==3.7',
        'lz4==4.3.3',
        'paho-mqtt==1.6.1',
        'requests==2.32.0',
        'urllib3==1.26.18',
        'httpx==0.27.0',
        'pydantic==2.6.3',
        'deepmerge==1.1.1',
        'aiocron==1.8',
    ],
)
