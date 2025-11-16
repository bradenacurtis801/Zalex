# UploadApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**deleteDocumentApiDocumentsDocumentIdDelete**](UploadApi.md#deletedocumentapidocumentsdocumentiddelete) | **DELETE** /api/documents/{document_id} | Delete Document |
| [**downloadDocumentApiDocumentsDocumentIdDownloadGet**](UploadApi.md#downloaddocumentapidocumentsdocumentiddownloadget) | **GET** /api/documents/{document_id}/download | Download Document |
| [**getDocumentContentApiDocumentsDocumentIdContentGet**](UploadApi.md#getdocumentcontentapidocumentsdocumentidcontentget) | **GET** /api/documents/{document_id}/content | Get Document Content |
| [**getPdfPagesApiDocumentsDocumentIdPagesGet**](UploadApi.md#getpdfpagesapidocumentsdocumentidpagesget) | **GET** /api/documents/{document_id}/pages | Get Pdf Pages |
| [**uploadFilesApiUploadPost**](UploadApi.md#uploadfilesapiuploadpost) | **POST** /api/upload | Upload Files |



## deleteDocumentApiDocumentsDocumentIdDelete

> any deleteDocumentApiDocumentsDocumentIdDelete(documentId)

Delete Document

Delete a document and all its associated data (admin only).  Args:     document_id: Document ID (SHA256 hash)     upload_service: Upload service instance     current_user: Authenticated admin user  Returns:     Success message with deletion details

### Example

```ts
import {
  Configuration,
  UploadApi,
} from '';
import type { DeleteDocumentApiDocumentsDocumentIdDeleteRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new UploadApi(config);

  const body = {
    // string
    documentId: documentId_example,
  } satisfies DeleteDocumentApiDocumentsDocumentIdDeleteRequest;

  try {
    const data = await api.deleteDocumentApiDocumentsDocumentIdDelete(body);
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

**any**

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


## downloadDocumentApiDocumentsDocumentIdDownloadGet

> any downloadDocumentApiDocumentsDocumentIdDownloadGet(documentId)

Download Document

Download a document file.  Args:     document_id: Document ID (SHA256 hash)     pdf_service: PDF service instance     current_user: Authenticated user  Returns:     File download response

### Example

```ts
import {
  Configuration,
  UploadApi,
} from '';
import type { DownloadDocumentApiDocumentsDocumentIdDownloadGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new UploadApi(config);

  const body = {
    // string
    documentId: documentId_example,
  } satisfies DownloadDocumentApiDocumentsDocumentIdDownloadGetRequest;

  try {
    const data = await api.downloadDocumentApiDocumentsDocumentIdDownloadGet(body);
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

**any**

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


## getDocumentContentApiDocumentsDocumentIdContentGet

> any getDocumentContentApiDocumentsDocumentIdContentGet(documentId)

Get Document Content

Get the content of a document for viewing.  Args:     document_id: Document ID (SHA256 hash)     pdf_service: PDF service instance     current_user: Authenticated user  Returns:     File content or text content

### Example

```ts
import {
  Configuration,
  UploadApi,
} from '';
import type { GetDocumentContentApiDocumentsDocumentIdContentGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new UploadApi(config);

  const body = {
    // string
    documentId: documentId_example,
  } satisfies GetDocumentContentApiDocumentsDocumentIdContentGetRequest;

  try {
    const data = await api.getDocumentContentApiDocumentsDocumentIdContentGet(body);
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

**any**

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


## getPdfPagesApiDocumentsDocumentIdPagesGet

> any getPdfPagesApiDocumentsDocumentIdPagesGet(documentId, pages)

Get Pdf Pages

Get PDF pages with caching - first check cache, then convert if needed. Can fetch specific pages or all pages.  Args:     document_id: Document ID (SHA256 hash)     pages: Optional comma-separated list of page numbers (1-based) to fetch     pdf_service: PDF service instance     current_user: Authenticated user  Returns:     JSON with page information and image data

### Example

```ts
import {
  Configuration,
  UploadApi,
} from '';
import type { GetPdfPagesApiDocumentsDocumentIdPagesGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new UploadApi(config);

  const body = {
    // string
    documentId: documentId_example,
    // string | Comma-separated list of page numbers to fetch (e.g., \'1,3,5\'). If not provided, returns all pages. (optional)
    pages: pages_example,
  } satisfies GetPdfPagesApiDocumentsDocumentIdPagesGetRequest;

  try {
    const data = await api.getPdfPagesApiDocumentsDocumentIdPagesGet(body);
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
| **pages** | `string` | Comma-separated list of page numbers to fetch (e.g., \&#39;1,3,5\&#39;). If not provided, returns all pages. | [Optional] [Defaults to `undefined`] |

### Return type

**any**

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


## uploadFilesApiUploadPost

> UploadResponse uploadFilesApiUploadPost(files)

Upload Files

Handles the file upload and initiates the processing pipeline.  Only PDF and image files (.pdf, .jpg, .jpeg, .png) are supported. Text files (.txt) are explicitly rejected.

### Example

```ts
import {
  Configuration,
  UploadApi,
} from '';
import type { UploadFilesApiUploadPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new UploadApi(config);

  const body = {
    // Array<Blob>
    files: /path/to/file.txt,
  } satisfies UploadFilesApiUploadPostRequest;

  try {
    const data = await api.uploadFilesApiUploadPost(body);
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
| **files** | `Array<Blob>` |  | |

### Return type

[**UploadResponse**](UploadResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: `multipart/form-data`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

