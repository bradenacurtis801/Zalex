
# OCRLineData

Line-level OCR data with bounding box information.

## Properties

Name | Type
------------ | -------------
`text` | string
`confidence` | number
`bbox` | { [key: string]: number; }
`words` | [Array&lt;OCRWordData&gt;](OCRWordData.md)
`blockNum` | number
`parNum` | number
`lineNum` | number

## Example

```typescript
import type { OCRLineData } from ''

// TODO: Update the object below with actual values
const example = {
  "text": null,
  "confidence": null,
  "bbox": null,
  "words": null,
  "blockNum": null,
  "parNum": null,
  "lineNum": null,
} satisfies OCRLineData

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as OCRLineData
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


