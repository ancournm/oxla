import json
from fastapi.openapi.utils import get_openapi
from app.main import app

def export_openapi_schema():
    """Export OpenAPI schema to JSON file"""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Save to file
    with open("docs/openapi_schema.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    # Convert to Postman collection
    postman_collection = convert_to_postman(openapi_schema)
    
    # Save Postman collection
    with open("docs/postman/oxlas_suite_postman.json", "w") as f:
        json.dump(postman_collection, f, indent=2)
    
    print("OpenAPI schema and Postman collection exported successfully")

def convert_to_postman(openapi_schema):
    """Convert OpenAPI schema to Postman collection format"""
    postman_collection = {
        "info": {
            "name": openapi_schema["info"]["title"],
            "description": openapi_schema["info"]["description"],
            "version": openapi_schema["info"]["version"]
        },
        "item": []
    }
    
    # Group endpoints by tags
    endpoints_by_tag = {}
    
    for path, methods in openapi_schema["paths"].items():
        for method, details in methods.items():
            tags = details.get("tags", ["default"])
            tag = tags[0] if tags else "default"
            
            if tag not in endpoints_by_tag:
                endpoints_by_tag[tag] = []
            
            endpoint = {
                "name": details.get("summary", f"{method.upper()} {path}"),
                "request": {
                    "method": method.upper(),
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        },
                        {
                            "key": "Authorization",
                            "value": "Bearer YOUR_TOKEN_HERE"
                        }
                    ],
                    "url": {
                        "raw": "http://localhost:8000" + path,
                        "protocol": "http",
                        "host": ["localhost", "8000"],
                        "path": path.strip("/").split("/")
                    }
                }
            }
            
            # Add request body if present
            if "requestBody" in details:
                schema = details["requestBody"]["content"]["application/json"]["schema"]
                endpoint["request"]["body"] = {
                    "mode": "raw",
                    "raw": json.dumps(get_example_from_schema(schema)),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
            
            # Add query parameters if present
            if "parameters" in details:
                endpoint["request"]["url"]["query"] = []
                for param in details["parameters"]:
                    if param["in"] == "query":
                        endpoint["request"]["url"]["query"].append({
                            "key": param["name"],
                            "value": param.get("example", ""),
                            "description": param.get("description", "")
                        })
            
            endpoints_by_tag[tag].append(endpoint)
    
    # Convert to Postman items
    for tag, endpoints in endpoints_by_tag.items():
        postman_collection["item"].append({
            "name": tag,
            "item": endpoints
        })
    
    return postman_collection

def get_example_from_schema(schema):
    """Generate example data from JSON schema"""
    example = {}
    
    if "$ref" in schema:
        # Handle references (simplified)
        return {}
    
    schema_type = schema.get("type", "object")
    
    if schema_type == "object":
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            example[prop_name] = get_example_from_schema(prop_schema)
    elif schema_type == "array":
        items = schema.get("items", {})
        example = [get_example_from_schema(items)]
    elif schema_type == "string":
        example = schema.get("example", "string")
    elif schema_type == "integer":
        example = schema.get("example", 0)
    elif schema_type == "boolean":
        example = schema.get("example", True)
    elif schema_type == "number":
        example = schema.get("example", 0.0)
    
    return example

if __name__ == "__main__":
    export_openapi_schema()