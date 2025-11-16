
# PerformanceMetricsMetadata

Metadata about model performance.

## Properties

Name | Type
------------ | -------------
`trainAccuracy` | number
`testAccuracy` | number
`trainConfidence` | [ConfidenceMetrics](ConfidenceMetrics.md)
`testConfidence` | [ConfidenceMetrics](ConfidenceMetrics.md)

## Example

```typescript
import type { PerformanceMetricsMetadata } from ''

// TODO: Update the object below with actual values
const example = {
  "trainAccuracy": null,
  "testAccuracy": null,
  "trainConfidence": null,
  "testConfidence": null,
} satisfies PerformanceMetricsMetadata

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PerformanceMetricsMetadata
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


