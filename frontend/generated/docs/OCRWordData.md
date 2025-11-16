
# OCRWordData

Word-level OCR data with bounding box information.

## Properties

Name | Type
------------ | -------------
`text` | string
`confidence` | number
`bbox` | { [key: string]: number; }
`blockNum` | number
`parNum` | number
`lineNum` | number
`wordNum` | number

## Example

```typescript
import type { OCRWordData } from ''

// TODO: Update the object below with actual values
const example = {
  "text": null,
  "confidence": null,
  "bbox": null,
  "blockNum": null,
  "parNum": null,
  "lineNum": null,
  "wordNum": null,
} satisfies OCRWordData

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as OCRWordData
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


