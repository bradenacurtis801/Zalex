'use client'

import React, { useState, useEffect, useRef } from 'react'
import OCROverlay from './OCROverlay'
import type { OCRDataResponse } from '@/generated/models/OCRDataResponse'

interface OCRPageProps {
  pageData: OCRDataResponse
  showWords?: boolean
  showLines?: boolean
  confidenceFilter?: number
  onTextHover?: (text: string, confidence: number) => void
  onBoundingBox?: (x: number, y: number, width: number, height: number, color: string) => void
  pdfBoundingBox?: {x: number, y: number, width: number, height: number, color: string} | null
  className?: string
}

export default function OCRPage({
  pageData,
  showWords = true,
  showLines = false,
  confidenceFilter = 0,
  onTextHover,
  onBoundingBox,
  pdfBoundingBox,
  className = ''
}: OCRPageProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [viewMode, setViewMode] = useState<'raw' | 'full'>('raw')
  const [debugInfo, setDebugInfo] = useState<{
    text: string
    confidence: number
    type: 'word' | 'line'
    blockNum: number
    parNum: number
    lineNum: number
    wordNum?: number
    bbox: { left: number, top: number, width: number, height: number }
  } | null>(null)

  const handleTextClick = (text: string, confidence: number, bbox: { left: number, top: number, width: number, height: number }) => {
    
    // Check if bbox coordinates are proportional (0.0 to 1.0) or absolute pixels
    const isProportional = bbox.left <= 1.0 && bbox.top <= 1.0 && bbox.width <= 1.0 && bbox.height <= 1.0
    
    // Find the text block info from the OCR data by text matching only
    const wordData = pageData.wordsData?.find(word => word.text === text)
    
    const lineData = pageData.linesData?.find(line => line.text === text)
    
    if (wordData) {
      setDebugInfo({
        text: wordData.text,
        confidence: wordData.confidence,
        type: 'word',
        blockNum: wordData.blockNum,
        parNum: wordData.parNum,
        lineNum: wordData.lineNum,
        wordNum: wordData.wordNum,
        bbox: {
          left: wordData.bbox.left,
          top: wordData.bbox.top,
          width: wordData.bbox.width,
          height: wordData.bbox.height
        }
      })
    } else if (lineData) {
      setDebugInfo({
        text: lineData.text,
        confidence: lineData.confidence,
        type: 'line',
        blockNum: lineData.blockNum,
        parNum: lineData.parNum,
        lineNum: lineData.lineNum,
        bbox: {
          left: lineData.bbox.left,
          top: lineData.bbox.top,
          width: lineData.bbox.width,
          height: lineData.bbox.height
        }
      })
    } else {
      console.log(`❌ No matching data found for text: "${text}"`)
      console.log(`📊 Available words:`, pageData.wordsData?.length || 0)
      console.log(`📊 Available lines:`, pageData.linesData?.length || 0)
    }
  }


  return (
    <div 
      ref={containerRef}
      className={`relative bg-black text-white min-h-screen p-4 ${className}`}
    >
      {/* Page Header */}
      <div className="sticky top-0 bg-gray-800 p-2 mb-4 rounded">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-semibold">OCR Page {pageData.pageNumber + 1}</h3>
          <div className="text-sm text-gray-300">
            {pageData.totalWords || 0} words, {pageData.totalLines || 0} lines
            <span className="ml-2 text-green-400">
              {((pageData.confidenceScore || 0) * 100).toFixed(1)}% confidence
            </span>
          </div>
        </div>
        
        {/* Navigation Menu */}
        <div className="flex space-x-2">
          <button
            onClick={() => setViewMode('raw')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              viewMode === 'raw' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
            }`}
          >
            Raw Text
          </button>
          <button
            onClick={() => setViewMode('full')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              viewMode === 'full' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
            }`}
          >
            Full Text
          </button>
        </div>
      </div>

      {/* Content based on view mode */}
      {viewMode === 'raw' ? (
        /* Raw Text - Scaled and positioned text blocks */
        <div className="relative">
          <OCROverlay
            pageData={pageData}
            showWords={showWords}
            showLines={showLines}
            confidenceFilter={confidenceFilter}
            onTextHover={onTextHover}
            onBoundingBox={onBoundingBox}
            onTextClick={handleTextClick}
          />
          
          {/* PDF Bounding Box Overlay */}
        {pdfBoundingBox && (
          (() => {
            // Get the original image dimensions from the OCR data
            const originalImageWidth = pageData.originalImageWidth || 1227  // Fallback to default if not available
            const originalImageHeight = pageData.originalImageHeight || 2163  // Fallback to default if not available
            
            // Get the actual container dimensions from the OCR page
            const containerWidth = containerRef.current?.clientWidth || 800  // Actual OCR page display width
            const containerHeight = containerRef.current?.clientHeight || 1000  // Actual OCR page display height
            
            // Calculate proportions (ratios) of the bounding box relative to original image
            const xRatio = pdfBoundingBox.x / originalImageWidth
            const yRatio = pdfBoundingBox.y / originalImageHeight
            const widthRatio = pdfBoundingBox.width / originalImageWidth
            const heightRatio = pdfBoundingBox.height / originalImageHeight
            
            // Apply the same proportions to the current display size
            const scaledX = xRatio * containerWidth
            const scaledY = yRatio * containerHeight
            const scaledWidth = widthRatio * containerWidth
            const scaledHeight = heightRatio * containerHeight
            
            console.log(`📐 OCR Proportional scaling:`, {
              original: { x: pdfBoundingBox.x, y: pdfBoundingBox.y, w: pdfBoundingBox.width, h: pdfBoundingBox.height },
              ratios: { x: xRatio.toFixed(3), y: yRatio.toFixed(3), w: widthRatio.toFixed(3), h: heightRatio.toFixed(3) },
              scaled: { x: scaledX.toFixed(1), y: scaledY.toFixed(1), w: scaledWidth.toFixed(1), h: scaledHeight.toFixed(1) },
              image: { original: `${originalImageWidth}×${originalImageHeight}`, display: `${containerWidth}×${containerHeight}` },
              containerRef: containerRef.current ? 'available' : 'null'
            })
            
            return (
              <div
                className="absolute border-2 pointer-events-none z-10"
                style={{
                  left: scaledX,
                  top: scaledY,
                  width: scaledWidth,
                  height: scaledHeight,
                  borderColor: pdfBoundingBox.color,
                  backgroundColor: `${pdfBoundingBox.color}20`
                }}
              />
            )
          })()
        )}
        </div>
      ) : (
        /* Full Text - Plain text in a single paragraph */
        <div className="bg-gray-900 p-4 rounded-lg">
          <div className="text-gray-100 leading-relaxed whitespace-pre-wrap">
            {pageData.fullText || 'No text available'}
          </div>
        </div>
      )}

      {/* Global Debug Info Display */}
      {debugInfo && (
        <div className="fixed top-4 right-4 bg-black text-white text-xs px-4 py-3 rounded-lg z-50 shadow-2xl border border-gray-500 max-w-sm">
          <div className="flex justify-between items-start mb-2">
            <div className="font-bold text-sm">{debugInfo.text}</div>
            <button
              onClick={() => setDebugInfo(null)}
              className="text-gray-400 hover:text-white ml-2 text-lg leading-none"
              title="Close debug info"
            >
              ×
            </button>
          </div>
          <div className="text-xs mb-1">
            {debugInfo.type === 'word' ? 'Word' : 'Line'} • {(debugInfo.confidence * 100).toFixed(1)}% confidence
          </div>
          <div className="text-xs mb-1">
            Block {debugInfo.blockNum}, Par {debugInfo.parNum}, Line {debugInfo.lineNum}
            {debugInfo.wordNum !== undefined && `, Word ${debugInfo.wordNum}`}
          </div>
          <div className="text-xs text-gray-300">
            Bounds: {debugInfo.bbox.left.toFixed(0)}, {debugInfo.bbox.top.toFixed(0)} ({debugInfo.bbox.width.toFixed(0)}×{debugInfo.bbox.height.toFixed(0)})
          </div>
        </div>
      )}

      {/* Full Text Display - Commented out */}
      {/* <div className="mt-8 bg-gray-900 p-4 rounded">
        <h4 className="text-lg font-semibold mb-2">Full Text:</h4>
        <div className="text-sm text-gray-300 whitespace-pre-wrap">
          {pageData.fullText || 'No text available'}
        </div>
      </div> */}
    </div>
  )
}
