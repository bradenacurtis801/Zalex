
# TaskSummaryResponse

Task summary with counts by status

## Properties

Name | Type
------------ | -------------
`totalTasks` | number
`pending` | number
`processing` | number
`completed` | number
`failed` | number

## Example

```typescript
import type { TaskSummaryResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "totalTasks": null,
  "pending": null,
  "processing": null,
  "completed": null,
  "failed": null,
} satisfies TaskSummaryResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as TaskSummaryResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


