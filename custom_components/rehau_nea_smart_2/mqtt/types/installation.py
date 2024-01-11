from pydantic import BaseModel
from typing import List

class Cooling(BaseModel):
    normal: int
    reduced: int

class Heating(BaseModel):
    normal: int
    reduced: int
    standby: int

class Setpoints(BaseModel):
    cooling: Cooling
    heating: Heating
    min: int
    max: int

class Channel(BaseModel):
    id: str
    target_temperature: int
    current_temperature: int
    energy_level: int
    operating_mode: int
    setpoints: Setpoints

class Zone(BaseModel):
    id: str
    name: str
    number: int
    channels: List[Channel]

class Group(BaseModel):
    id: str
    group_name: str
    zones: List[Zone]

class Installation(BaseModel):
    id: str
    unique: str
    global_energy_level: int
    operating_mode: int
    groups: List[Group]