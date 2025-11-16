
# TrainingMetadata

Complete training metadata for TFIDF classifier.

## Properties

Name | Type
------------ | -------------
`modelId` | string
`trainingTimestamp` | string
`modelType` | string
`trainingData` | [TrainingDataMetadata](TrainingDataMetadata.md)
`featureExtraction` | [FeatureExtractionMetadata](FeatureExtractionMetadata.md)
`modelParameters` | [ModelParametersMetadata](ModelParametersMetadata.md)
`performanceMetrics` | [PerformanceMetricsMetadata](PerformanceMetricsMetadata.md)
`trainDataHashes` | Array&lt;string&gt;

## Example

```typescript
import type { TrainingMetadata } from ''

// TODO: Update the object below with actual values
const example = {
  "modelId": null,
  "trainingTimestamp": null,
  "modelType": null,
  "trainingData": null,
  "featureExtraction": null,
  "modelParameters": null,
  "performanceMetrics": null,
  "trainDataHashes": null,
} satisfies TrainingMetadata

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as TrainingMetadata
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


