
# TrainingDataMetadata

Metadata about the training data used.

## Properties

Name | Type
------------ | -------------
`totalDocuments` | number
`totalCategories` | number
`trainSamples` | number
`testSamples` | number
`testSplitPercentage` | number
`distribution` | { [key: string]: { [key: string]: DistributionValueValue; }; }

## Example

```typescript
import type { TrainingDataMetadata } from ''

// TODO: Update the object below with actual values
const example = {
  "totalDocuments": null,
  "totalCategories": null,
  "trainSamples": null,
  "testSamples": null,
  "testSplitPercentage": null,
  "distribution": null,
} satisfies TrainingDataMetadata

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as TrainingDataMetadata
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


