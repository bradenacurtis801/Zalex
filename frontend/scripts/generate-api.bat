@echo off
REM Generate TypeScript API client from FastAPI OpenAPI spec
REM Make sure your FastAPI backend is running on localhost:5000

echo Generating API client from FastAPI OpenAPI spec...

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set GENERATED_DIR=%SCRIPT_DIR%..\generated

REM Generate TypeScript Fetch client
npx @openapitools/openapi-generator-cli generate ^
  -i http://localhost:5000/openapi.json ^
  -g typescript-fetch ^
  -o "%GENERATED_DIR%" ^
  --additional-properties=typescriptThreePlus=true,supportsES6=true,withInterfaces=true

echo API client generated successfully!
echo Generated files are in %GENERATED_DIR%
