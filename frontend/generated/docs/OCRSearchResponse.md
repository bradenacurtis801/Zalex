
# OCRSearchResponse

Response for OCR text search.

## Properties

Name | Type
------------ | -------------
`documentId` | string
`query` | string
`caseSensitive` | boolean
`totalMatches` | number
`matches` | [Array&lt;OCRSearchMatch&gt;](OCRSearchMatch.md)

## Example

```typescript
import type { OCRSearchResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "documentId": null,
  "query": null,
  "caseSensitive": null,
  "totalMatches": null,
  "matches": null,
} satisfies OCRSearchResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as OCRSearchResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


