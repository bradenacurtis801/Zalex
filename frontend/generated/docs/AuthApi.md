# AuthApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**adminResetPasswordApiAuthUsersUserIdResetPasswordPost**](AuthApi.md#adminresetpasswordapiauthusersuseridresetpasswordpost) | **POST** /api/auth/users/{user_id}/reset-password | Admin Reset Password |
| [**changePasswordApiAuthChangePasswordPost**](AuthApi.md#changepasswordapiauthchangepasswordpost) | **POST** /api/auth/change-password | Change Password |
| [**createUserApiAuthUsersPost**](AuthApi.md#createuserapiauthuserspost) | **POST** /api/auth/users | Create User |
| [**deleteUserApiAuthUsersUserIdDelete**](AuthApi.md#deleteuserapiauthusersuseriddelete) | **DELETE** /api/auth/users/{user_id} | Delete User |
| [**getAllUsersApiAuthUsersGet**](AuthApi.md#getallusersapiauthusersget) | **GET** /api/auth/users | Get All Users |
| [**getCurrentUserInfoApiAuthMeGet**](AuthApi.md#getcurrentuserinfoapiauthmeget) | **GET** /api/auth/me | Get Current User Info |
| [**getUserApiAuthUsersUserIdGet**](AuthApi.md#getuserapiauthusersuseridget) | **GET** /api/auth/users/{user_id} | Get User |
| [**loginApiAuthLoginPost**](AuthApi.md#loginapiauthloginpost) | **POST** /api/auth/login | Login |
| [**updateUserApiAuthUsersUserIdPut**](AuthApi.md#updateuserapiauthusersuseridput) | **PUT** /api/auth/users/{user_id} | Update User |
| [**updateUserRoleApiAuthUsersUserIdRolePut**](AuthApi.md#updateuserroleapiauthusersuseridroleput) | **PUT** /api/auth/users/{user_id}/role | Update User Role |



## adminResetPasswordApiAuthUsersUserIdResetPasswordPost

> any adminResetPasswordApiAuthUsersUserIdResetPasswordPost(userId, adminPasswordReset)

Admin Reset Password

Reset user password (admin only) - no current password required

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { AdminResetPasswordApiAuthUsersUserIdResetPasswordPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new AuthApi(config);

  const body = {
    // number
    userId: 56,
    // AdminPasswordReset
    adminPasswordReset: ...,
  } satisfies AdminResetPasswordApiAuthUsersUserIdResetPasswordPostRequest;

  try {
    const data = await api.adminResetPasswordApiAuthUsersUserIdResetPasswordPost(body);
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
| **userId** | `number` |  | [Defaults to `undefined`] |
| **adminPasswordReset** | [AdminPasswordReset](AdminPasswordReset.md) |  | |

### Return type

**any**

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


## changePasswordApiAuthChangePasswordPost

> any changePasswordApiAuthChangePasswordPost(userChangePassword)

Change Password

Change current user\&#39;s password

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { ChangePasswordApiAuthChangePasswordPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new AuthApi(config);

  const body = {
    // UserChangePassword
    userChangePassword: ...,
  } satisfies ChangePasswordApiAuthChangePasswordPostRequest;

  try {
    const data = await api.changePasswordApiAuthChangePasswordPost(body);
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
| **userChangePassword** | [UserChangePassword](UserChangePassword.md) |  | |

### Return type

**any**

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


## createUserApiAuthUsersPost

> UserResponse createUserApiAuthUsersPost(userCreate)

Create User

Create a new user (admin only)

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { CreateUserApiAuthUsersPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new AuthApi(config);

  const body = {
    // UserCreate
    userCreate: ...,
  } satisfies CreateUserApiAuthUsersPostRequest;

  try {
    const data = await api.createUserApiAuthUsersPost(body);
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
| **userCreate** | [UserCreate](UserCreate.md) |  | |

### Return type

[**UserResponse**](UserResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## deleteUserApiAuthUsersUserIdDelete

> any deleteUserApiAuthUsersUserIdDelete(userId)

Delete User

Delete user (admin only) - cannot delete self

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { DeleteUserApiAuthUsersUserIdDeleteRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new AuthApi(config);

  const body = {
    // number
    userId: 56,
  } satisfies DeleteUserApiAuthUsersUserIdDeleteRequest;

  try {
    const data = await api.deleteUserApiAuthUsersUserIdDelete(body);
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
| **userId** | `number` |  | [Defaults to `undefined`] |

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


## getAllUsersApiAuthUsersGet

> Array&lt;UserResponse&gt; getAllUsersApiAuthUsersGet(skip, limit)

Get All Users

Get all users (admin only)

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { GetAllUsersApiAuthUsersGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new AuthApi(config);

  const body = {
    // number (optional)
    skip: 56,
    // number (optional)
    limit: 56,
  } satisfies GetAllUsersApiAuthUsersGetRequest;

  try {
    const data = await api.getAllUsersApiAuthUsersGet(body);
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

[**Array&lt;UserResponse&gt;**](UserResponse.md)

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


## getCurrentUserInfoApiAuthMeGet

> UserResponse getCurrentUserInfoApiAuthMeGet()

Get Current User Info

Get current user information

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { GetCurrentUserInfoApiAuthMeGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new AuthApi(config);

  try {
    const data = await api.getCurrentUserInfoApiAuthMeGet();
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

[**UserResponse**](UserResponse.md)

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


## getUserApiAuthUsersUserIdGet

> UserResponse getUserApiAuthUsersUserIdGet(userId)

Get User

Get user by ID (admin only)

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { GetUserApiAuthUsersUserIdGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new AuthApi(config);

  const body = {
    // number
    userId: 56,
  } satisfies GetUserApiAuthUsersUserIdGetRequest;

  try {
    const data = await api.getUserApiAuthUsersUserIdGet(body);
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
| **userId** | `number` |  | [Defaults to `undefined`] |

### Return type

[**UserResponse**](UserResponse.md)

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


## loginApiAuthLoginPost

> TokenResponse loginApiAuthLoginPost(userLogin)

Login

Login and get session token

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { LoginApiAuthLoginPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new AuthApi();

  const body = {
    // UserLogin
    userLogin: ...,
  } satisfies LoginApiAuthLoginPostRequest;

  try {
    const data = await api.loginApiAuthLoginPost(body);
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
| **userLogin** | [UserLogin](UserLogin.md) |  | |

### Return type

[**TokenResponse**](TokenResponse.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## updateUserApiAuthUsersUserIdPut

> UserResponse updateUserApiAuthUsersUserIdPut(userId, userUpdate)

Update User

Update user (admin only) - cannot change own role

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { UpdateUserApiAuthUsersUserIdPutRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new AuthApi(config);

  const body = {
    // number
    userId: 56,
    // UserUpdate
    userUpdate: ...,
  } satisfies UpdateUserApiAuthUsersUserIdPutRequest;

  try {
    const data = await api.updateUserApiAuthUsersUserIdPut(body);
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
| **userId** | `number` |  | [Defaults to `undefined`] |
| **userUpdate** | [UserUpdate](UserUpdate.md) |  | |

### Return type

[**UserResponse**](UserResponse.md)

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


## updateUserRoleApiAuthUsersUserIdRolePut

> UserResponse updateUserRoleApiAuthUsersUserIdRolePut(userId, role)

Update User Role

Update user role (admin only) - cannot change own role

### Example

```ts
import {
  Configuration,
  AuthApi,
} from '';
import type { UpdateUserRoleApiAuthUsersUserIdRolePutRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new AuthApi(config);

  const body = {
    // number
    userId: 56,
    // UserRole
    role: ...,
  } satisfies UpdateUserRoleApiAuthUsersUserIdRolePutRequest;

  try {
    const data = await api.updateUserRoleApiAuthUsersUserIdRolePut(body);
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
| **userId** | `number` |  | [Defaults to `undefined`] |
| **role** | `UserRole` |  | [Defaults to `undefined`] [Enum: user, admin] |

### Return type

[**UserResponse**](UserResponse.md)

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

