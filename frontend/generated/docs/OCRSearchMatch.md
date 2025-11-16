
# OCRSearchMatch

Search match result.

## Properties

Name | Type
------------ | -------------
`pageNumber` | number
`position` | number
`text` | string
`confidence` | number

## Example

```typescript
import type { OCRSearchMatch } from ''

// TODO: Update the object below with actual values
const example = {
  "pageNumber": null,
  "position": null,
  "text": null,
  "confidence": null,
} satisfies OCRSearchMatch

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as OCRSearchMatch
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


