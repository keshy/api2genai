import json
from enum import Enum
from typing import AnyStr, Dict, List, Any
import logging


class F_Type(Enum):
    OPENAI = "OpenAI"
    MCP = "MCP"
    VERTEX = "Vertex"


class Base:
    def __init__(self, openapi_spec_loc: str, f_type: F_Type, spec_loc: str, code_gen_loc: str):
        self.openapi_spec_loc = openapi_spec_loc
        self.f_type = f_type
        self.tool_spec_loc = spec_loc
        self.code_gen_loc = code_gen_loc
        with open(self.openapi_spec_loc, 'r') as r:
            txt = r.read()
            self.openapi_spec_dict = json.loads(txt)
        self.logger = logging.getLogger("api2genai")

    def gen_spec(self) -> List[Dict[str, Any]]:
        pass

    def gen_code(self) -> AnyStr:
        pass

    def process(self):
        specs = self.gen_spec()
        with open(self.tool_spec_loc, 'w') as w:
            w.write(json.dumps(specs))
        code_str = self.gen_code()
        with open(self.code_gen_loc, 'w') as w:
            w.write(code_str)
