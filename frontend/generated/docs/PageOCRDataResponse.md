
# PageOCRDataResponse

Response for getting OCR data for a specific page.

## Properties

Name | Type
------------ | -------------
`id` | number
`documentId` | string
`pageNumber` | number
`fullText` | string
`confidenceScore` | number
`totalWords` | number
`totalLines` | number
`wordsData` | [Array&lt;OCRWordData&gt;](OCRWordData.md)
`linesData` | [Array&lt;OCRLineData&gt;](OCRLineData.md)
`createdAt` | Date

## Example

```typescript
import type { PageOCRDataResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "id": null,
  "documentId": null,
  "pageNumber": null,
  "fullText": null,
  "confidenceScore": null,
  "totalWords": null,
  "totalLines": null,
  "wordsData": null,
  "linesData": null,
  "createdAt": null,
} satisfies PageOCRDataResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PageOCRDataResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


