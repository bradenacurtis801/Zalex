
# FeedbackSummary

Summary of feedback corrections.

## Properties

Name | Type
------------ | -------------
`totalCorrections` | number
`correctionsByCategory` | { [key: string]: any; }
`lastUpdated` | Date
`modelVersion` | string

## Example

```typescript
import type { FeedbackSummary } from ''

// TODO: Update the object below with actual values
const example = {
  "totalCorrections": null,
  "correctionsByCategory": null,
  "lastUpdated": null,
  "modelVersion": null,
} satisfies FeedbackSummary

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as FeedbackSummary
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


