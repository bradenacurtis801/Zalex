
# ClassifierInfoResponse

Response model for classifier information including training metadata.

## Properties

Name | Type
------------ | -------------
`name` | string
`metadata` | { [key: string]: any; }
`type` | string
`modelName` | string
`classNames` | Array&lt;string&gt;
`isInitialized` | boolean
`trainingMetadata` | [TrainingMetadata](TrainingMetadata.md)

## Example

```typescript
import type { ClassifierInfoResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "name": null,
  "metadata": null,
  "type": null,
  "modelName": null,
  "classNames": null,
  "isInitialized": null,
  "trainingMetadata": null,
} satisfies ClassifierInfoResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ClassifierInfoResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


