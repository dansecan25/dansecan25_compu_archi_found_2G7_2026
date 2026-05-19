# __init__.py – inicialización del paquete 'pipelineEtapas'

from .Decode import Decode
from .RegisterFile import RegisterFile
from .Fetch import Fetch
from .Execute import Execute
from .EtapaStore import EtapaStore
from .latencias_config import get_stage_latency, get_instruction_latency

__all__ = [
    "Decode",
    "RegisterFile",
    "Fetch",
    "Execute",
    "EtapaStore",
    "get_stage_latency",
    "get_instruction_latency",
]