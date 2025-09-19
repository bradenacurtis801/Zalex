@echo off
REM Generate TypeScript API client from FastAPI OpenAPI spec
REM Make sure your FastAPI backend is running on localhost:5000

echo Generating API client from FastAPI OpenAPI spec...

REM Generate TypeScript Fetch client
npx @openapitools/openapi-generator-cli generate ^
  -i http://localhost:5000/openapi.json ^
  -g typescript-fetch ^
  -o ./generated ^
  --additional-properties=typescriptThreePlus=true,supportsES6=true,withInterfaces=true

echo API client generated successfully!
echo Generated files are in ./generated/
