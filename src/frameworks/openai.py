from typing import Dict, Any, List, AnyStr

from src.frameworks import Base, F_Type


class OpenAIGenerator(Base):

    def __init__(self, openapi_spec_loc: str, spec_loc: str, code_gen_loc: str):
        super().__init__(openapi_spec_loc, F_Type.OPENAI, spec_loc, code_gen_loc)
        self.functions = []

    @staticmethod
    def resolve_reference(schema: Dict[str, Any], openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolves a $ref pointer in an OpenAPI schema.

        Args:
            schema: The schema containing the $ref.
            openapi_spec: The entire OpenAPI specification.

        Returns:
            The resolved schema, or the original schema if no $ref is present.
        """
        if '$ref' in schema:
            ref_path = schema['$ref']
            parts = ref_path.split('#/')
            if len(parts) > 1:
                path_parts = parts[1].split('/')
                resolved_schema = openapi_spec
                for part in path_parts:
                    if part:
                        resolved_schema = resolved_schema.get(part)
                        if resolved_schema is None:
                            return schema  # Return original if path is invalid
                return resolved_schema
            else:
                return schema
        else:
            return schema

    def gen_spec(self) -> List[Dict[str, Any]]:
        """
        Translates an OpenAPI specification (2.0 or 3.0) into a list of OpenAI function specifications.
        This version includes all combinations of optional parameters and captures response schemas.
        It also resolves $ref pointers.

        Args:
            openapi_spec: The OpenAPI specification in JSON format.

        Returns:
            A list of OpenAI function specifications, formatted for OpenAI.
        """
        functions = []
        paths = openapi_spec.get('paths', {})
        openapi_version = openapi_spec.get('openapi', openapi_spec.get('swagger', '2.0'))
        components = openapi_spec.get('components', {}).get('schemas', {})  # OpenAPI 3.0 components

        for path, operations in paths.items():
            for method, operation in operations.items():
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    continue

                operation_id = operation.get('operationId')
                if not operation_id:
                    continue

                description = operation.get('description', '')
                parameters = operation.get('parameters', [])

                required_params = [p for p in parameters if p.get('required', False)]
                optional_params = [p for p in parameters if not p.get('required', False)]

                # Generate function specs for all combinations of optional parameters
                for i in range(2 ** len(optional_params)):
                    selected_optional_params = []
                    param_names = []
                    param_descriptions = []
                    for j, opt_param in enumerate(optional_params):
                        if (i >> j) & 1:
                            selected_optional_params.append(opt_param)
                            param_names.append(opt_param['name'])
                            param_descriptions.append(f"{opt_param['name']}: {opt_param['description']}")

                    all_params = required_params + selected_optional_params
                    if not all_params:
                        all_params = []

                    openai_params = []
                    for param in all_params:
                        param_schema = param.get('schema', {})
                        param_schema = self.resolve_reference(param_schema, openapi_spec)  # Resolve $ref
                        param_type = param_schema.get('type', param.get('type', 'string'))
                        if param_type == 'integer':
                            param_type = 'number'
                        elif param_type == 'file':
                            continue  # Skip file parameters for now
                        elif param_type == 'array':
                            param_type = 'array'  # Keep it as array
                        elif param_type == 'object':
                            param_type = 'object'
                        openai_params.append({
                            'name': param['name'],
                            'type': param_type,
                            'description': param.get('description', ''),
                            'required': param.get('required', False),
                            'in': param.get('in')
                        })

                    function_name_suffix = ""
                    for param_name in param_names:
                        function_name_suffix += f"_{param_name}"
                    if function_name_suffix:
                        generated_operation_id = f"{operation_id}{function_name_suffix}"
                    else:
                        generated_operation_id = operation_id

                    # Get the response schema
                    responses = operation.get('responses', {})
                    response_200 = responses.get('200', responses.get('default', {}))  # handles default
                    response_schema = response_200.get('schema', {})
                    response_schema = self.resolve_reference(response_schema, openapi_spec)  # Resolve $ref for response

                    # Handle OpenAPI 3.0 response
                    if openapi_version.startswith('3.'):
                        if 'content' in response_200:
                            for content_type in response_200['content']:
                                response_schema = response_200['content'][content_type].get('schema', {})
                                response_schema = self.resolve_reference(response_schema,
                                                                         openapi_spec)  # Resolve $ref in content
                                break  # Just take the first content type

                    response_type = response_schema.get('type', 'object')  # Default to object
                    if response_type == 'integer':
                        response_type = 'number'
                    elif response_type == 'array':
                        response_type = 'array'
                    elif response_type == 'object':
                        response_type = 'object'

                    openai_function_spec = {
                        'name': generated_operation_id,
                        'description': description,
                        'parameters': {
                            'type': 'object',
                            'properties': {p['name']: {'type': p['type'], 'description': p['description']} for p in
                                           openai_params},
                            'required': [p['name'] for p in openai_params if p['required']]
                        },
                        'responses': {  # added response
                            'type': 'object',
                            'properties': {
                                'response': {
                                    'type': response_type,
                                    'description': 'Response from the API call',
                                    # Include full schema for better type info
                                    'schema': response_schema
                                }
                            }

                        },
                    }

                    functions.append({
                        'type': 'function',
                        'function': openai_function_spec
                    })
        return functions

    def gen_code(self) -> AnyStr:
        """
        Generates Python code from an OpenAPI specification.

        Args:
            openapi_spec: The OpenAPI specification in JSON format.

        Returns:
            The generated Python code.
        """
        base_url = openapi_spec.get('host', 'http://localhost') + openapi_spec.get('basePath', '')

        code = """
    import requests
    from typing import Dict, Any, Optional
    
    def get_bearer_token() -> str:
        # Replace with your actual bearer token retrieval logic
        return "YOUR_BEARER_TOKEN"
    
    def get_url(base_url: str, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        url = base_url + path
        if params:
            query_params = '&'.join([f'{key}={value}' for key, value in params.items() if value is not None])
            if query_params:
                url += '?' + query_params
        return url
    
    def _call_api(url: str, method: str, headers: Dict[str, str], json: Optional[Dict[str, Any]] = None) -> Any:
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=json)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=json)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=json)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
    
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            if response.status_code == 204:
                return None
    
            return response.json() if response.content else None
    
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None
        """

        for func in self.functions:
            function_spec = func['function']
            operation_id = function_spec['name']
            description = function_spec['description']
            parameters = function_spec['parameters']
            path = func['path']
            method = func['method']

            code_snippet = f"""
        def {operation_id}("""
            if parameters['properties']:
                code_snippet += ', '.join(
                    [f"{name}: {prop['type']}" for name, prop in parameters['properties'].items()])
            code_snippet += f""") -> Any:
            \"\"\"
            {description}
            \"\"\"
            base_url = "{base_url}"
            path = "{path}"
            method = "{method}"
            headers = {{"Authorization": f"Bearer {{get_bearer_token()}}"}}
            url_params = {{}}
            body_params = {{}}
        
            """
            if parameters['properties']:
                for name, prop in parameters['properties'].items():
                    if 'in' not in [p for p in func['function']['parameters'] if p['name'] == name][0]:
                        # checking the 'in'
                        continue
                    param_in = [p for p in func['function']['parameters'] if p['name'] == name][0]['in']
                    if param_in == 'path':
                        code_snippet += f"    path = path.replace('{{{name}}}', str({name}))\\n"
                    elif param_in == 'query':
                        code_snippet += f"    url_params['{name}'] = {name}\\n"
                    elif param_in == 'body':
                        code_snippet += f"    body_params['{name}'] = {name}\\n"

            code_snippet += f"""
            url = get_url(base_url, path, url_params if url_params else None)
            return _call_api(url, method, headers, json=body_params if body_params else None)
            """
            code += code_snippet

        return code


# Example usage (replace with your OpenAPI specification)
openapi_spec = {
    "swagger": "2.0",
    "host": "api.example.com",
    "basePath": "/v1",
    "paths": {
        "/users/{userId}": {
            "get": {
                "operationId": "getUser",
                "description": "Retrieves a user by ID.",
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "required": True,
                        "type": "integer"
                    },
                    {
                        "name": "includeDetails",
                        "in": "query",
                        "required": False,
                        "type": "boolean",
                        "description": "Include extra user details"
                    },
                    {
                        "name": "excludeSensitive",
                        "in": "query",
                        "required": False,
                        "type": "boolean",
                        "description": "Exclude sensitive information"
                    }
                ]
            },
            "post": {
                "operationId": "createUser",
                "description": "Creates a user.",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string"
                                },
                                "email": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                ]
            }
        }
    }
}
