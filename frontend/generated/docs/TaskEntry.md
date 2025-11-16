
# TaskEntry

Individual task entry for API responses

## Properties

Name | Type
------------ | -------------
`id` | number
`documentId` | string
`filename` | string
`status` | string
`error` | string
`createdAt` | Date
`updatedAt` | Date

## Example

```typescript
import type { TaskEntry } from ''

// TODO: Update the object below with actual values
const example = {
  "id": null,
  "documentId": null,
  "filename": null,
  "status": null,
  "error": null,
  "createdAt": null,
  "updatedAt": null,
} satisfies TaskEntry

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as TaskEntry
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


