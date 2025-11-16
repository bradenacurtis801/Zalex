# FeedbackApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getFeedbackSummaryApiFeedbackSummaryGet**](FeedbackApi.md#getfeedbacksummaryapifeedbacksummaryget) | **GET** /api/feedback/summary | Get Feedback Summary |
| [**reclassifyDocumentApiFeedbackReclassifyPost**](FeedbackApi.md#reclassifydocumentapifeedbackreclassifypost) | **POST** /api/feedback/reclassify | Reclassify Document |



## getFeedbackSummaryApiFeedbackSummaryGet

> FeedbackSummary getFeedbackSummaryApiFeedbackSummaryGet(skip, limit)

Get Feedback Summary

Get a summary of feedback corrections and model updates.  Args:     skip: Number of feedback records to skip (for pagination)     limit: Maximum number of feedback records to return (for pagination)     feedback_service: Feedback service instance     current_user: Authenticated user  Returns:     FeedbackSummary with correction statistics

### Example

```ts
import {
  Configuration,
  FeedbackApi,
} from '';
import type { GetFeedbackSummaryApiFeedbackSummaryGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new FeedbackApi(config);

  const body = {
    // number (optional)
    skip: 56,
    // number (optional)
    limit: 56,
  } satisfies GetFeedbackSummaryApiFeedbackSummaryGetRequest;

  try {
    const data = await api.getFeedbackSummaryApiFeedbackSummaryGet(body);
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
| **skip** | `number` |  | [Optional] [Defaults to `0`] |
| **limit** | `number` |  | [Optional] [Defaults to `100`] |

### Return type

[**FeedbackSummary**](FeedbackSummary.md)

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


## reclassifyDocumentApiFeedbackReclassifyPost

> ReclassificationResponse reclassifyDocumentApiFeedbackReclassifyPost(reclassificationRequest)

Reclassify Document

Reclassify a document based on user feedback.  Args:     request: Reclassification request with document details     feedback_service: Feedback service instance     current_user: Authenticated user  Returns:     ReclassificationResponse with processing results

### Example

```ts
import {
  Configuration,
  FeedbackApi,
} from '';
import type { ReclassifyDocumentApiFeedbackReclassifyPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new FeedbackApi(config);

  const body = {
    // ReclassificationRequest
    reclassificationRequest: ...,
  } satisfies ReclassifyDocumentApiFeedbackReclassifyPostRequest;

  try {
    const data = await api.reclassifyDocumentApiFeedbackReclassifyPost(body);
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
| **reclassificationRequest** | [ReclassificationRequest](ReclassificationRequest.md) |  | |

### Return type

[**ReclassificationResponse**](ReclassificationResponse.md)

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

