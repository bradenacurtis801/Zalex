'use client'

import { useState, useEffect } from 'react'
import type { OCRDataResponse } from '@/generated/models/OCRDataResponse'
import TextBlock, { createWordTextBlock, createLineTextBlock } from './TextBlock'

interface OCROverlayProps {
  pageData: OCRDataResponse
  showWords?: boolean
  showLines?: boolean
  confidenceFilter?: number
  className?: string
  onTextHover?: (text: string, confidence: number) => void
  onBoundingBox?: (x: number, y: number, width: number, height: number, color: string) => void
  onTextClick?: (text: string, confidence: number, bbox: { left: number, top: number, width: number, height: number }) => void
}

export default function OCROverlay({
  pageData,
  showWords = true,
  showLines = false,
  confidenceFilter = 0,
  className = '',
  onTextHover,
  onBoundingBox,
  onTextClick
}: OCROverlayProps) {
  const { wordsData = [], linesData = [] } = pageData
  
  // Get scaling factors for TextBlocks - scale to fit within container
  const originalImageWidth = pageData.originalImageWidth || 1227
  const originalImageHeight = pageData.originalImageHeight || 2163
  
  // Use a more conservative scaling to ensure TextBlocks fit within the container
  // Scale down to fit within a reasonable container size
  const maxContainerWidth = 700   // Conservative width to fit in half-screen
  const maxContainerHeight = 900  // Conservative height to fit in half-screen
  
  const ocrScaleX = maxContainerWidth / originalImageWidth
  const ocrScaleY = maxContainerHeight / originalImageHeight

  // Create TextBlocks with debug logging
  const wordBlocks = showWords && Array.isArray(wordsData) 
    ? wordsData.filter(word => word && word.confidence >= confidenceFilter)
    : []
  
  const lineBlocks = showLines && Array.isArray(linesData) 
    ? linesData.filter(line => line && line.confidence >= confidenceFilter)
    : []

  return (
    <div className={`absolute inset-0 ${className}`}>
      {/* Word Overlays */}
      {wordBlocks.map(word => createWordTextBlock(word, onTextClick, ocrScaleX, ocrScaleY))}

      {/* Line Overlays */}
      {lineBlocks.map(line => createLineTextBlock(line, onTextClick, ocrScaleX, ocrScaleY))}
    </div>
  )
}
