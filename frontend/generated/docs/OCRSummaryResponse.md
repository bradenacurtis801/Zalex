
# OCRSummaryResponse

Response for document text summary.

## Properties

Name | Type
------------ | -------------
`documentId` | string
`summary` | [DocumentTextSummary](DocumentTextSummary.md)

## Example

```typescript
import type { OCRSummaryResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "documentId": null,
  "summary": null,
} satisfies OCRSummaryResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as OCRSummaryResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


