"""Set up the Rehau MQTT client."""
from setuptools import setup, find_packages

setup(
    name='rehau_mqtt_client',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'asyncio==3.4.3',
        'certifi==2023.11.17',
        'charset-normalizer==3.3.2',
        'future==0.18.3',
        'idna==3.6',
        'lz4==4.3.3',
        'lzstring @ git+https://github.com/marcel-dancak/lz-string-python.git@c2a8e14ec55e6917ac9d8b41486df2a9ee79f5bb',
        'paho-mqtt==1.6.1',
        'requests==2.31.0',
        'urllib3==2.1.0',
        'schedule==1.1.0',
    ],
)
