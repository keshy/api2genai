# api2genai
Translation tool to generate tool specifications or different genAI models. 


### Usage

```shell

usage: 
          /\
         /  \
        /----\ 
       /      \ 
      -------- \ 
      \        /
       \  ()  /
        \    /
         ----
           ||
           ||
        +------+
        | API2 |
        | GEN  |
        +------+
           ||
           ||
         /----\
        /      \
       /        \
      /----------\
        
API2GEN: Your OpenAPI to OpenAI Function Converter
       [-h] -s SPEC -t {OpenAI,MCP,Vertex} [-f TOOL_SPEC] [-c CODE]

options:
  -h, --help            show this help message and exit
  -s SPEC, --spec SPEC  OpenAPI spec file to be processed
  -t {OpenAI,MCP,Vertex}, --tool {OpenAI,MCP,Vertex}
                        The tool family to use for generation of spec and code
  -f TOOL_SPEC, --tool_spec TOOL_SPEC
                        Location on disk where the tool spec needs to be saved
  -c CODE, --code CODE  Location on disk where the generated code needs to be saved


```