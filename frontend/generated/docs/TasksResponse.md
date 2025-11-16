
# TasksResponse

List of tasks for current user with pagination

## Properties

Name | Type
------------ | -------------
`tasks` | [Array&lt;TaskEntry&gt;](TaskEntry.md)
`total` | number
`page` | number
`pageSize` | number
`totalPages` | number

## Example

```typescript
import type { TasksResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "tasks": null,
  "total": null,
  "page": null,
  "pageSize": null,
  "totalPages": null,
} satisfies TasksResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as TasksResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


