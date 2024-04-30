from pathlib import Path
from dotenv import dotenv_values
from pydantic import BaseModel, validator, fields

class Config(BaseModel):
  unconverted_data_dir: Path
  converted_data_dir: Path
  processed_data_dir: Path
  psd_python_binary_path: Path
  psd_program_path: Path
  overrides_file_path: Path

  @validator('*', pre=True)
  def make_path(cls, v, field: fields.ModelField):
    return Path(v)
  

def load_env_config(path: str|None = None) -> Config:
  config = dotenv_values(path)
  return Config.parse_obj(config)