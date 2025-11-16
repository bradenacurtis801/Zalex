# CategoryApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createCategoryApiCategoriesPost**](CategoryApi.md#createcategoryapicategoriespost) | **POST** /api/categories | Create Category |
| [**getAllCategoriesApiCategoriesGet**](CategoryApi.md#getallcategoriesapicategoriesget) | **GET** /api/categories | Get All Categories |
| [**getCategoriesSummaryApiCategoriesSummaryGet**](CategoryApi.md#getcategoriessummaryapicategoriessummaryget) | **GET** /api/categories/summary | Get Categories Summary |
| [**getDocumentsByCategoryApiCategoriesCategoryGet**](CategoryApi.md#getdocumentsbycategoryapicategoriescategoryget) | **GET** /api/categories/{category} | Get Documents By Category |
| [**getTrainingMetricsApiCategoriesTrainingMetricsGet**](CategoryApi.md#gettrainingmetricsapicategoriestrainingmetricsget) | **GET** /api/categories/training-metrics | Get Training Metrics |



## createCategoryApiCategoriesPost

> { [key: string]: any; } createCategoryApiCategoriesPost(name, files, description)

Create Category

Create a new category with training documents (admin only).  Args:     name: Category name     description: Category description (optional)     files: PDF files to use as training data for this category      Returns:     Dictionary with category info and uploaded document count

### Example

```ts
import {
  Configuration,
  CategoryApi,
} from '';
import type { CreateCategoryApiCategoriesPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new CategoryApi(config);

  const body = {
    // string
    name: name_example,
    // Array<Blob>
    files: /path/to/file.txt,
    // string (optional)
    description: description_example,
  } satisfies CreateCategoryApiCategoriesPostRequest;

  try {
    const data = await api.createCategoryApiCategoriesPost(body);
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
| **name** | `string` |  | [Defaults to `undefined`] |
| **files** | `Array<Blob>` |  | |
| **description** | `string` |  | [Optional] [Defaults to `undefined`] |

### Return type

**{ [key: string]: any; }**

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


## getAllCategoriesApiCategoriesGet

> CategoriesResponse getAllCategoriesApiCategoriesGet(skip, limit)

Get All Categories

Get all available categories and their documents.

### Example

```ts
import {
  Configuration,
  CategoryApi,
} from '';
import type { GetAllCategoriesApiCategoriesGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new CategoryApi(config);

  const body = {
    // number (optional)
    skip: 56,
    // number (optional)
    limit: 56,
  } satisfies GetAllCategoriesApiCategoriesGetRequest;

  try {
    const data = await api.getAllCategoriesApiCategoriesGet(body);
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

[**CategoriesResponse**](CategoriesResponse.md)

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


## getCategoriesSummaryApiCategoriesSummaryGet

> { [key: string]: any; } getCategoriesSummaryApiCategoriesSummaryGet()

Get Categories Summary

Get a summary of document counts per category.

### Example

```ts
import {
  Configuration,
  CategoryApi,
} from '';
import type { GetCategoriesSummaryApiCategoriesSummaryGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new CategoryApi(config);

  try {
    const data = await api.getCategoriesSummaryApiCategoriesSummaryGet();
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

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getDocumentsByCategoryApiCategoriesCategoryGet

> CategoryResponse getDocumentsByCategoryApiCategoriesCategoryGet(category, skip, limit)

Get Documents By Category

Get all documents in a specific category.

### Example

```ts
import {
  Configuration,
  CategoryApi,
} from '';
import type { GetDocumentsByCategoryApiCategoriesCategoryGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new CategoryApi(config);

  const body = {
    // string
    category: category_example,
    // number (optional)
    skip: 56,
    // number (optional)
    limit: 56,
  } satisfies GetDocumentsByCategoryApiCategoriesCategoryGetRequest;

  try {
    const data = await api.getDocumentsByCategoryApiCategoriesCategoryGet(body);
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
| **category** | `string` |  | [Defaults to `undefined`] |
| **skip** | `number` |  | [Optional] [Defaults to `0`] |
| **limit** | `number` |  | [Optional] [Defaults to `100`] |

### Return type

[**CategoryResponse**](CategoryResponse.md)

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


## getTrainingMetricsApiCategoriesTrainingMetricsGet

> ClassifierInfoResponse getTrainingMetricsApiCategoriesTrainingMetricsGet()

Get Training Metrics

Get training metrics for all categories (admin only).  Returns:     ClassifierInfoResponse with classifier information and training metadata.     Includes TrainingMetadata model with performance metrics, data distribution,     model parameters, and feature extraction settings.

### Example

```ts
import {
  Configuration,
  CategoryApi,
} from '';
import type { GetTrainingMetricsApiCategoriesTrainingMetricsGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new CategoryApi(config);

  try {
    const data = await api.getTrainingMetricsApiCategoriesTrainingMetricsGet();
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

[**ClassifierInfoResponse**](ClassifierInfoResponse.md)

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

