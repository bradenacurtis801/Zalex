
# OCRDataResponse

OCR data response for a single page.

## Properties

Name | Type
------------ | -------------
`id` | number
`pageNumber` | number
`fullText` | string
`confidenceScore` | number
`totalWords` | number
`totalLines` | number
`wordsData` | [Array&lt;OCRWordData&gt;](OCRWordData.md)
`linesData` | [Array&lt;OCRLineData&gt;](OCRLineData.md)
`originalImageWidth` | number
`originalImageHeight` | number
`createdAt` | Date

## Example

```typescript
import type { OCRDataResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "id": null,
  "pageNumber": null,
  "fullText": null,
  "confidenceScore": null,
  "totalWords": null,
  "totalLines": null,
  "wordsData": null,
  "linesData": null,
  "originalImageWidth": null,
  "originalImageHeight": null,
  "createdAt": null,
} satisfies OCRDataResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as OCRDataResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


