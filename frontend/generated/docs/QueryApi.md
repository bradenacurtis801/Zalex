# QueryApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**queryIndexApiQueryPost**](QueryApi.md#queryindexapiquerypost) | **POST** /api/query | Query Index |



## queryIndexApiQueryPost

> QueryResponse queryIndexApiQueryPost(queryRequest)

Query Index

Handles user queries, searches the index, and returns relevant results.

### Example

```ts
import {
  Configuration,
  QueryApi,
} from '';
import type { QueryIndexApiQueryPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new QueryApi(config);

  const body = {
    // QueryRequest
    queryRequest: ...,
  } satisfies QueryIndexApiQueryPostRequest;

  try {
    const data = await api.queryIndexApiQueryPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **queryRequest** | [QueryRequest](QueryRequest.md) |  | |

### Return type

[**QueryResponse**](QueryResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

