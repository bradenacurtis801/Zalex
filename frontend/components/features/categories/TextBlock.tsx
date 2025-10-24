'use client'

import React, { useState } from 'react'
import type { OCRWordData, OCRLineData } from '@/generated/models'

interface TextBlockProps {
  text: string
  confidence: number
  bbox: {
    left: number
    top: number
    width: number
    height: number
  }
  blockNum: number
  parNum: number
  lineNum: number
  wordNum?: number // Only for word blocks
  type: 'word' | 'line'
  onTextClick?: (text: string, confidence: number, bbox: { left: number, top: number, width: number, height: number }) => void
  className?: string
}

// Function to calculate optimal font size that fits within the bounding box
const calculateOptimalFontSize = (text: string, width: number, height: number): number => {
  // Calculate font size based on both width and height constraints
  const widthBasedSize = (width * 0.8) / text.length // Account for text length
  const heightBasedSize = height * 0.7 // Leave some padding
  
  // Use the smaller of the two to ensure text fits
  const optimalSize = Math.min(widthBasedSize, heightBasedSize)
  
  // Return the calculated size (no min/max constraints since we have zoom)
  return Math.max(1, optimalSize) // Only prevent negative or zero sizes
}

export default function TextBlock({
  text,
  confidence,
  bbox,
  blockNum,
  parNum,
  lineNum,
  wordNum,
  type,
  onTextClick,
  className = ''
}: TextBlockProps) {
  const [isLocalHovered, setIsLocalHovered] = useState(false)
  const [isClicked, setIsClicked] = useState(false)
  
  // Debug logging for TextBlock creation
//   console.log(`🔧 TextBlock created:`, {
//     text: text.substring(0, 20) + (text.length > 20 ? '...' : ''),
//     type,
//     confidence: (confidence * 100).toFixed(1) + '%',
//     bbox: { left: bbox.left, top: bbox.top, width: bbox.width, height: bbox.height }
//   })
  
  const isCurrentlyHovered = isLocalHovered
  
  const handleMouseEnter = () => {
    setIsLocalHovered(true)
  }
  
  const handleMouseLeave = () => {
    setIsLocalHovered(false)
  }

  const handleClick = () => {
    setIsClicked(!isClicked)
    console.log(`🖱️ TextBlock clicked: "${text}"`, { 
      isClicked: !isClicked,
      text,
      confidence: (confidence * 100).toFixed(1) + '%',
      type,
      blockInfo: { blockNum, parNum, lineNum, wordNum }
    })
    
    // Call the callback to show debug info
    if (onTextClick) {
      onTextClick(text, confidence, bbox)
    }
  }
  
  // Color coding based on confidence
  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) return 'text-green-400' // High confidence
    if (conf >= 0.6) return 'text-yellow-400' // Medium confidence
    return 'text-red-400' // Low confidence
  }
  
  // Background color for hover state with smooth transitions
  const getHoverBgColor = () => {
    if (type === 'word') return 'bg-blue-500/30'
    return 'bg-green-500/30'
  }
  
  // Border color for hover state
  const getHoverBorderColor = () => {
    if (type === 'word') return 'border-blue-400'
    return 'border-green-400'
  }
  
  return (
    <div
      className={`
        absolute cursor-pointer transition-all duration-300 ease-in-out
        ${isCurrentlyHovered ? getHoverBorderColor() : 'border-transparent'}
        hover:shadow-lg
        ${className}
      `}
      style={{
        left: `${bbox.left}px`,
        top: `${bbox.top}px`,
        width: `${bbox.width}px`,
        height: `${bbox.height}px`
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
      title={`${text} (${(confidence * 100).toFixed(1)}% confidence)`}
    >
      {/* Text content */}
      <div className={`
        w-full h-full flex items-center justify-center
        transition-all duration-300 ease-in-out
        ${getConfidenceColor(confidence)}
        ${isCurrentlyHovered ? 'font-bold text-white' : ''}
        ${type === 'word' ? 'border-blue-300/50' : 'border-green-300/50'}
        ${isCurrentlyHovered ? 'border-opacity-100' : 'border-opacity-30'}
        ${isCurrentlyHovered ? getHoverBgColor() : 'bg-transparent'}
        rounded-sm
        ${isCurrentlyHovered ? 'shadow-md' : ''} 
      `}
      style={{
        fontSize: `${calculateOptimalFontSize(text, bbox.width, bbox.height)}px`,
        lineHeight: '1',
        textAlign: 'center',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: `${Math.max(0.5, Math.min(bbox.width, bbox.height) * 0.01)}px`
      }}>
        <span style={{ 
          maxWidth: '100%', 
          maxHeight: '100%',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {text}
        </span>
      </div>
      
      {/* Debug info is now handled globally by OCRPage */}
    </div>
  )
}

// Helper function to create TextBlock from OCRWordData
export function createWordTextBlock(
  word: OCRWordData,
  onTextClick?: (text: string, confidence: number, bbox: { left: number, top: number, width: number, height: number }) => void,
  scaleX: number = 1,
  scaleY: number = 1
) {
  return (
    <TextBlock
      key={`word-${word.blockNum}-${word.parNum}-${word.lineNum}-${word.wordNum}`}
      text={word.text}
      confidence={word.confidence}
      bbox={{
        left: word.bbox.left * scaleX,
        top: word.bbox.top * scaleY,
        width: word.bbox.width * scaleX,
        height: word.bbox.height * scaleY
      }}
      blockNum={word.blockNum}
      parNum={word.parNum}
      lineNum={word.lineNum}
      wordNum={word.wordNum}
      type="word"
      onTextClick={onTextClick}
    />
  )
}

// Helper function to create TextBlock from OCRLineData
export function createLineTextBlock(
  line: OCRLineData,
  onTextClick?: (text: string, confidence: number, bbox: { left: number, top: number, width: number, height: number }) => void,
  scaleX: number = 1,
  scaleY: number = 1
) {
  return (
    <TextBlock
      key={`line-${line.blockNum}-${line.parNum}-${line.lineNum}`}
      text={line.text}
      confidence={line.confidence}
      bbox={{
        left: line.bbox.left * scaleX,
        top: line.bbox.top * scaleY,
        width: line.bbox.width * scaleX,
        height: line.bbox.height * scaleY
      }}
      blockNum={line.blockNum}
      parNum={line.parNum}
      lineNum={line.lineNum}
      type="line"
      onTextClick={onTextClick}
    />
  )
}
