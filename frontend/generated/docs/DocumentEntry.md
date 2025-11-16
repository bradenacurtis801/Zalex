
# DocumentEntry


## Properties

Name | Type
------------ | -------------
`id` | string
`filename` | string
`category` | string
`confidence` | number
`timestamp` | string
`fileSize` | number
`mimeType` | string
`status` | string

## Example

```typescript
import type { DocumentEntry } from ''

// TODO: Update the object below with actual values
const example = {
  "id": null,
  "filename": null,
  "category": null,
  "confidence": null,
  "timestamp": null,
  "fileSize": null,
  "mimeType": null,
  "status": null,
} satisfies DocumentEntry

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as DocumentEntry
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


