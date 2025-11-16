
# DocumentOCRDataResponse

Response for getting all OCR data for a document.

## Properties

Name | Type
------------ | -------------
`documentId` | string
`totalPages` | number
`ocrData` | [Array&lt;OCRDataResponse&gt;](OCRDataResponse.md)

## Example

```typescript
import type { DocumentOCRDataResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "documentId": null,
  "totalPages": null,
  "ocrData": null,
} satisfies DocumentOCRDataResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as DocumentOCRDataResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


