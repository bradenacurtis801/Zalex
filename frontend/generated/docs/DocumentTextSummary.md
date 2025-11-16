
# DocumentTextSummary

Document text summary.

## Properties

Name | Type
------------ | -------------
`totalPages` | number
`totalWords` | number
`totalLines` | number
`averageConfidence` | number
`fullText` | string

## Example

```typescript
import type { DocumentTextSummary } from ''

// TODO: Update the object below with actual values
const example = {
  "totalPages": null,
  "totalWords": null,
  "totalLines": null,
  "averageConfidence": null,
  "fullText": null,
} satisfies DocumentTextSummary

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as DocumentTextSummary
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


