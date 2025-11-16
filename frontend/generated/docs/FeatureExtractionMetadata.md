
# FeatureExtractionMetadata

Metadata about feature extraction parameters.

## Properties

Name | Type
------------ | -------------
`vectorizerType` | string
`maxFeatures` | number
`ngramRange` | Array&lt;number&gt;
`minDf` | number
`maxDf` | number
`sublinearTf` | boolean
`vocabularySize` | number
`featureDim` | number

## Example

```typescript
import type { FeatureExtractionMetadata } from ''

// TODO: Update the object below with actual values
const example = {
  "vectorizerType": null,
  "maxFeatures": null,
  "ngramRange": null,
  "minDf": null,
  "maxDf": null,
  "sublinearTf": null,
  "vocabularySize": null,
  "featureDim": null,
} satisfies FeatureExtractionMetadata

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as FeatureExtractionMetadata
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


