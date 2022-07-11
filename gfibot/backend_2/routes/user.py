from typing import List

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from gfibot.collections import *
from ..models import GFIResponse

api = APIRouter()
logger = logging.getLogger(__name__)