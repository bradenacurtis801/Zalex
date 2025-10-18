import { useState } from 'react'
import { feedbackApi } from '@/api'
import { 
  ReclassificationRequest, 
  ReclassificationResponse, 
  FeedbackSummary 
} from '@/generated'

export function useFeedback() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const reclassifyDocument = async (request: ReclassificationRequest): Promise<ReclassificationResponse> => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await feedbackApi.reclassifyDocumentApiFeedbackReclassifyPost({
        reclassificationRequest: request
      })
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reclassify document'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const getFeedbackSummary = async (): Promise<FeedbackSummary> => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await feedbackApi.getFeedbackSummaryApiFeedbackSummaryGet()
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get feedback summary'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }


  return {
    loading,
    error,
    reclassifyDocument,
    getFeedbackSummary,
  }
}
