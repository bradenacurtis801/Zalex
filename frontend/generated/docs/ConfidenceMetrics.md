
# ConfidenceMetrics

Confidence score metrics.

## Properties

Name | Type
------------ | -------------
`mean` | number
`min` | number
`max` | number
`lowConfidenceCount` | number
`lowConfidencePercentage` | number

## Example

```typescript
import type { ConfidenceMetrics } from ''

// TODO: Update the object below with actual values
const example = {
  "mean": null,
  "min": null,
  "max": null,
  "lowConfidenceCount": null,
  "lowConfidencePercentage": null,
} satisfies ConfidenceMetrics

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ConfidenceMetrics
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


