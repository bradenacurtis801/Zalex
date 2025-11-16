# OcrApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getDocumentOcrDataApiDocumentsDocumentIdOcrGet**](OcrApi.md#getdocumentocrdataapidocumentsdocumentidocrget) | **GET** /api/documents/{document_id}/ocr | Get Document Ocr Data |
| [**getDocumentTextSummaryApiDocumentsDocumentIdOcrSummaryGet**](OcrApi.md#getdocumenttextsummaryapidocumentsdocumentidocrsummaryget) | **GET** /api/documents/{document_id}/ocr/summary | Get Document Text Summary |
| [**getPageOcrDataApiDocumentsDocumentIdOcrPagesPageNumberGet**](OcrApi.md#getpageocrdataapidocumentsdocumentidocrpagespagenumberget) | **GET** /api/documents/{document_id}/ocr/pages/{page_number} | Get Page Ocr Data |
| [**searchDocumentTextApiDocumentsDocumentIdOcrSearchGet**](OcrApi.md#searchdocumenttextapidocumentsdocumentidocrsearchget) | **GET** /api/documents/{document_id}/ocr/search | Search Document Text |



## getDocumentOcrDataApiDocumentsDocumentIdOcrGet

> DocumentOCRDataResponse getDocumentOcrDataApiDocumentsDocumentIdOcrGet(documentId)

Get Document Ocr Data

Get all OCR data for a document.  Args:     document_id: Document ID (SHA256 hash)     ocr_service: OCR service instance      Returns:     DocumentOCRDataResponse with all OCR data for the document

### Example

```ts
import {
  Configuration,
  OcrApi,
} from '';
import type { GetDocumentOcrDataApiDocumentsDocumentIdOcrGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new OcrApi(config);

  const body = {
    // string
    documentId: documentId_example,
  } satisfies GetDocumentOcrDataApiDocumentsDocumentIdOcrGetRequest;

  try {
    const data = await api.getDocumentOcrDataApiDocumentsDocumentIdOcrGet(body);
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
| **documentId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**DocumentOCRDataResponse**](DocumentOCRDataResponse.md)

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


## getDocumentTextSummaryApiDocumentsDocumentIdOcrSummaryGet

> OCRSummaryResponse getDocumentTextSummaryApiDocumentsDocumentIdOcrSummaryGet(documentId)

Get Document Text Summary

Get a summary of all text content in a document.  Args:     document_id: Document ID (SHA256 hash)     ocr_service: OCR service instance      Returns:     OCRSummaryResponse with document text summary

### Example

```ts
import {
  Configuration,
  OcrApi,
} from '';
import type { GetDocumentTextSummaryApiDocumentsDocumentIdOcrSummaryGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new OcrApi(config);

  const body = {
    // string
    documentId: documentId_example,
  } satisfies GetDocumentTextSummaryApiDocumentsDocumentIdOcrSummaryGetRequest;

  try {
    const data = await api.getDocumentTextSummaryApiDocumentsDocumentIdOcrSummaryGet(body);
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
| **documentId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**OCRSummaryResponse**](OCRSummaryResponse.md)

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


## getPageOcrDataApiDocumentsDocumentIdOcrPagesPageNumberGet

> PageOCRDataResponse getPageOcrDataApiDocumentsDocumentIdOcrPagesPageNumberGet(documentId, pageNumber)

Get Page Ocr Data

Get OCR data for a specific page of a document.  Args:     document_id: Document ID (SHA256 hash)     page_number: Page number (0-indexed)     ocr_service: OCR service instance      Returns:     PageOCRDataResponse with detailed OCR data for the specified page

### Example

```ts
import {
  Configuration,
  OcrApi,
} from '';
import type { GetPageOcrDataApiDocumentsDocumentIdOcrPagesPageNumberGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new OcrApi(config);

  const body = {
    // string
    documentId: documentId_example,
    // number
    pageNumber: 56,
  } satisfies GetPageOcrDataApiDocumentsDocumentIdOcrPagesPageNumberGetRequest;

  try {
    const data = await api.getPageOcrDataApiDocumentsDocumentIdOcrPagesPageNumberGet(body);
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
| **documentId** | `string` |  | [Defaults to `undefined`] |
| **pageNumber** | `number` |  | [Defaults to `undefined`] |

### Return type

[**PageOCRDataResponse**](PageOCRDataResponse.md)

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


## searchDocumentTextApiDocumentsDocumentIdOcrSearchGet

> OCRSearchResponse searchDocumentTextApiDocumentsDocumentIdOcrSearchGet(documentId, query, caseSensitive)

Search Document Text

Search for text within a document\&#39;s OCR data.  Args:     document_id: Document ID (SHA256 hash)     query: Text to search for     case_sensitive: Whether search should be case sensitive     ocr_service: OCR service instance      Returns:     OCRSearchResponse with search matches and metadata

### Example

```ts
import {
  Configuration,
  OcrApi,
} from '';
import type { SearchDocumentTextApiDocumentsDocumentIdOcrSearchGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new OcrApi(config);

  const body = {
    // string
    documentId: documentId_example,
    // string | Text to search for
    query: query_example,
    // boolean | Whether search should be case sensitive (optional)
    caseSensitive: true,
  } satisfies SearchDocumentTextApiDocumentsDocumentIdOcrSearchGetRequest;

  try {
    const data = await api.searchDocumentTextApiDocumentsDocumentIdOcrSearchGet(body);
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
| **documentId** | `string` |  | [Defaults to `undefined`] |
| **query** | `string` | Text to search for | [Defaults to `undefined`] |
| **caseSensitive** | `boolean` | Whether search should be case sensitive | [Optional] [Defaults to `false`] |

### Return type

[**OCRSearchResponse**](OCRSearchResponse.md)

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

