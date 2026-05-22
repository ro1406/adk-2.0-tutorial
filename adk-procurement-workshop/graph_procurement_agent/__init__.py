"""Procurement graph workflow agent package."""

import sys
from pathlib import Path

_workshop_root = Path(__file__).resolve().parent.parent
if str(_workshop_root) not in sys.path:
    sys.path.insert(0, str(_workshop_root))

import workshop_logging

workshop_logging.configure_quiet_console()

from . import agent

root_agent = agent.root_agent
