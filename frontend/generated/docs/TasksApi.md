# TasksApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**deleteTaskApiTasksTaskIdDelete**](TasksApi.md#deletetaskapitaskstaskiddelete) | **DELETE** /api/tasks/{task_id} | Delete Task |
| [**deleteTaskApiTasksTaskIdDelete_0**](TasksApi.md#deletetaskapitaskstaskiddelete_0) | **DELETE** /api/tasks/{task_id} | Delete Task |
| [**deleteTasksApiTasksDelete**](TasksApi.md#deletetasksapitasksdelete) | **DELETE** /api/tasks | Delete Tasks |
| [**deleteTasksApiTasksDelete_0**](TasksApi.md#deletetasksapitasksdelete_0) | **DELETE** /api/tasks | Delete Tasks |
| [**getTaskSummaryApiTasksSummaryGet**](TasksApi.md#gettasksummaryapitaskssummaryget) | **GET** /api/tasks/summary | Get Task Summary |
| [**getTaskSummaryApiTasksSummaryGet_0**](TasksApi.md#gettasksummaryapitaskssummaryget_0) | **GET** /api/tasks/summary | Get Task Summary |
| [**getUserTasksApiTasksGet**](TasksApi.md#getusertasksapitasksget) | **GET** /api/tasks | Get User Tasks |
| [**getUserTasksApiTasksGet_0**](TasksApi.md#getusertasksapitasksget_0) | **GET** /api/tasks | Get User Tasks |



## deleteTaskApiTasksTaskIdDelete

> { [key: string]: any; } deleteTaskApiTasksTaskIdDelete(taskId)

Delete Task

Delete a processing task for the current user.  Args:     task_id: Task ID to delete      Returns:     Success message

### Example

```ts
import {
  Configuration,
  TasksApi,
} from '';
import type { DeleteTaskApiTasksTaskIdDeleteRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new TasksApi(config);

  const body = {
    // number
    taskId: 56,
  } satisfies DeleteTaskApiTasksTaskIdDeleteRequest;

  try {
    const data = await api.deleteTaskApiTasksTaskIdDelete(body);
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
| **taskId** | `number` |  | [Defaults to `undefined`] |

### Return type

**{ [key: string]: any; }**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## deleteTaskApiTasksTaskIdDelete_0

> { [key: string]: any; } deleteTaskApiTasksTaskIdDelete_0(taskId)

Delete Task

Delete a processing task for the current user.  Args:     task_id: Task ID to delete      Returns:     Success message

### Example

```ts
import {
  Configuration,
  TasksApi,
} from '';
import type { DeleteTaskApiTasksTaskIdDelete0Request } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new TasksApi(config);

  const body = {
    // number
    taskId: 56,
  } satisfies DeleteTaskApiTasksTaskIdDelete0Request;

  try {
    const data = await api.deleteTaskApiTasksTaskIdDelete_0(body);
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
| **taskId** | `number` |  | [Defaults to `undefined`] |

### Return type

**{ [key: string]: any; }**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## deleteTasksApiTasksDelete

> { [key: string]: any; } deleteTasksApiTasksDelete(bulkDeleteTasksRequest)

Delete Tasks

Delete multiple processing tasks for the current user in a single request.  Args:     request: BulkDeleteTasksRequest containing list of task IDs      Returns:     Success message with deletion results

### Example

```ts
import {
  Configuration,
  TasksApi,
} from '';
import type { DeleteTasksApiTasksDeleteRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new TasksApi(config);

  const body = {
    // BulkDeleteTasksRequest
    bulkDeleteTasksRequest: ...,
  } satisfies DeleteTasksApiTasksDeleteRequest;

  try {
    const data = await api.deleteTasksApiTasksDelete(body);
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
| **bulkDeleteTasksRequest** | [BulkDeleteTasksRequest](BulkDeleteTasksRequest.md) |  | |

### Return type

**{ [key: string]: any; }**

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


## deleteTasksApiTasksDelete_0

> { [key: string]: any; } deleteTasksApiTasksDelete_0(bulkDeleteTasksRequest)

Delete Tasks

Delete multiple processing tasks for the current user in a single request.  Args:     request: BulkDeleteTasksRequest containing list of task IDs      Returns:     Success message with deletion results

### Example

```ts
import {
  Configuration,
  TasksApi,
} from '';
import type { DeleteTasksApiTasksDelete0Request } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new TasksApi(config);

  const body = {
    // BulkDeleteTasksRequest
    bulkDeleteTasksRequest: ...,
  } satisfies DeleteTasksApiTasksDelete0Request;

  try {
    const data = await api.deleteTasksApiTasksDelete_0(body);
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
| **bulkDeleteTasksRequest** | [BulkDeleteTasksRequest](BulkDeleteTasksRequest.md) |  | |

### Return type

**{ [key: string]: any; }**

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


## getTaskSummaryApiTasksSummaryGet

> TaskSummaryResponse getTaskSummaryApiTasksSummaryGet()

Get Task Summary

Get task summary (counts by status) for the current user.  Returns:     TaskSummaryResponse with counts of tasks by status

### Example

```ts
import {
  Configuration,
  TasksApi,
} from '';
import type { GetTaskSummaryApiTasksSummaryGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new TasksApi(config);

  try {
    const data = await api.getTaskSummaryApiTasksSummaryGet();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**TaskSummaryResponse**](TaskSummaryResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getTaskSummaryApiTasksSummaryGet_0

> TaskSummaryResponse getTaskSummaryApiTasksSummaryGet_0()

Get Task Summary

Get task summary (counts by status) for the current user.  Returns:     TaskSummaryResponse with counts of tasks by status

### Example

```ts
import {
  Configuration,
  TasksApi,
} from '';
import type { GetTaskSummaryApiTasksSummaryGet0Request } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new TasksApi(config);

  try {
    const data = await api.getTaskSummaryApiTasksSummaryGet_0();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**TaskSummaryResponse**](TaskSummaryResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getUserTasksApiTasksGet

> TasksResponse getUserTasksApiTasksGet(page, pageSize)

Get User Tasks

Get paginated processing tasks for the current user.  Args:     page: Page number (default: 1)     page_size: Number of items per page (default: 20, max: 100)  Returns:     TasksResponse with paginated list of tasks

### Example

```ts
import {
  Configuration,
  TasksApi,
} from '';
import type { GetUserTasksApiTasksGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new TasksApi(config);

  const body = {
    // number | Page number (1-indexed) (optional)
    page: 56,
    // number | Number of items per page (optional)
    pageSize: 56,
  } satisfies GetUserTasksApiTasksGetRequest;

  try {
    const data = await api.getUserTasksApiTasksGet(body);
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
| **page** | `number` | Page number (1-indexed) | [Optional] [Defaults to `1`] |
| **pageSize** | `number` | Number of items per page | [Optional] [Defaults to `20`] |

### Return type

[**TasksResponse**](TasksResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getUserTasksApiTasksGet_0

> TasksResponse getUserTasksApiTasksGet_0(page, pageSize)

Get User Tasks

Get paginated processing tasks for the current user.  Args:     page: Page number (default: 1)     page_size: Number of items per page (default: 20, max: 100)  Returns:     TasksResponse with paginated list of tasks

### Example

```ts
import {
  Configuration,
  TasksApi,
} from '';
import type { GetUserTasksApiTasksGet0Request } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new TasksApi(config);

  const body = {
    // number | Page number (1-indexed) (optional)
    page: 56,
    // number | Number of items per page (optional)
    pageSize: 56,
  } satisfies GetUserTasksApiTasksGet0Request;

  try {
    const data = await api.getUserTasksApiTasksGet_0(body);
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
| **page** | `number` | Page number (1-indexed) | [Optional] [Defaults to `1`] |
| **pageSize** | `number` | Number of items per page | [Optional] [Defaults to `20`] |

### Return type

[**TasksResponse**](TasksResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

