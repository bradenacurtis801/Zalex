
# ModelParametersMetadata

Metadata about model parameters.

## Properties

Name | Type
------------ | -------------
`modelType` | string
`alpha` | number
`c` | number
`solver` | string
`classWeight` | string

## Example

```typescript
import type { ModelParametersMetadata } from ''

// TODO: Update the object below with actual values
const example = {
  "modelType": null,
  "alpha": null,
  "c": null,
  "solver": null,
  "classWeight": null,
} satisfies ModelParametersMetadata

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ModelParametersMetadata
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


