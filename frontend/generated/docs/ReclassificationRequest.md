
# ReclassificationRequest

Request model for document reclassification feedback.

## Properties

Name | Type
------------ | -------------
`id` | string
`filename` | string
`currentCategory` | string
`newCategory` | string
`confidence` | number
`userComment` | string

## Example

```typescript
import type { ReclassificationRequest } from ''

// TODO: Update the object below with actual values
const example = {
  "id": null,
  "filename": null,
  "currentCategory": null,
  "newCategory": null,
  "confidence": null,
  "userComment": null,
} satisfies ReclassificationRequest

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ReclassificationRequest
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


