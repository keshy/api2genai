import argparse

from frameworks import F_Type
from frameworks.openai import OpenAIGenerator

EXEC_MAP = {
    F_Type.OPENAI.value: OpenAIGenerator
}

if __name__ == '__main__':
    api2gen_art = """
          /\
         /  \\
        /----\\ \\
       /      \\ \\
      --------  \\
      \\        /
       \\  ()  /
        \\    /
         ----
           ||
           ||
        +----------+
        | OpenAPI  |
        | GENAI    |
        +----------+
           ||
           ||
         /----\\
        /      \\
       /        \\
      /----------\\
        """

    args = argparse.ArgumentParser(f"{api2gen_art}\nAPI2GEN: Your OpenAPI to OpenAI Function Converter",
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
    args.add_argument('-s', '--spec', help="OpenAPI spec file to be processed", required=True, type=str)
    args.add_argument('-t', '--tool', help="The tool family to use for generation of spec and code", required=True,
                      choices=[member.value for member in F_Type], type=str)
    args.add_argument('-f', '--tool_spec', help="Location on disk where the tool spec needs to be saved",
                      default='../output/tools/spec.json', type=str)
    args.add_argument('-c', '--code', help="Location on disk where the generated code needs to be saved",
                      default='../output/tools/code.py', type=str)
    arguments = args.parse_args()

    generator = EXEC_MAP.get(arguments.tool)(arguments.spec, arguments.tool_spec, arguments.code)
    generator.process()
