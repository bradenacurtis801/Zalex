'use client'

import React, { useState, useEffect, useRef } from 'react'
import { createWordTextBlock, createLineTextBlock } from './TextBlock'
import type { OCRDataResponse } from '@/generated/models/OCRDataResponse'

interface OCRPageProps {
  pageData: OCRDataResponse
  className?: string
}

export default function OCRPage({
  pageData,
  className = ''
}: OCRPageProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLDivElement>(null)
  const [viewMode, setViewMode] = useState<'raw' | 'full'>('raw')
  const [displayMode, setDisplayMode] = useState<'words' | 'lines'>('words')
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
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

  // Reset pan when page data changes (new page navigation)
  useEffect(() => {
    setPan({ x: 0, y: 0 })
    setZoom(1)
  }, [pageData])

  // Zoom and pan handlers
  const handleZoom = (delta: number) => {
    const newZoom = Math.max(0.1, Math.min(5, zoom + delta))
    setZoom(newZoom)
  }

  const handleZoomTowardsMouse = (delta: number, mouseX: number, mouseY: number) => {
    const newZoom = Math.max(0.1, Math.min(5, zoom + delta))
    
    if (newZoom === zoom) return // No change in zoom
    
    // Calculate the point in the content that the mouse is pointing to
    const contentX = (mouseX - pan.x) / zoom
    const contentY = (mouseY - pan.y) / zoom
    
    // Calculate new pan to keep that point under the mouse
    const newPanX = mouseX - (contentX * newZoom)
    const newPanY = mouseY - (contentY * newZoom)
    
    setZoom(newZoom)
    setPan({ x: newPanX, y: newPanY })
  }

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -0.1 : 0.1
    
    // Get mouse position relative to the canvas
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return
    
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    
    // Calculate zoom towards mouse position
    handleZoomTowardsMouse(delta, mouseX, mouseY)
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) { // Left mouse button
      setIsDragging(true)
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      const newPanX = e.clientX - dragStart.x
      const newPanY = e.clientY - dragStart.y
      
      // Calculate base pan range from actual text content bounds
      const calculateTextBounds = () => {
        const words = pageData.wordsData || []
        const lines = pageData.linesData || []
        
        if (words.length === 0 && lines.length === 0) {
          return { width: 800, height: 800, minX: 0, maxX: 800, minY: 0, maxY: 800 } // Fallback if no text data
        }
        
        let minX = Infinity
        let maxX = -Infinity
        let minY = Infinity
        let maxY = -Infinity
        
        // Check word bounds
        words.forEach(word => {
          if (word.bbox) {
            minX = Math.min(minX, word.bbox.left)
            maxX = Math.max(maxX, word.bbox.left + word.bbox.width)
            minY = Math.min(minY, word.bbox.top)
            maxY = Math.max(maxY, word.bbox.top + word.bbox.height)
          }
        })
        
        // Check line bounds
        lines.forEach(line => {
          if (line.bbox) {
            minX = Math.min(minX, line.bbox.left)
            maxX = Math.max(maxX, line.bbox.left + line.bbox.width)
            minY = Math.min(minY, line.bbox.top)
            maxY = Math.max(maxY, line.bbox.top + line.bbox.height)
          }
        })
        
        return {
          width: maxX - minX,
          height: maxY - minY,
          minX,
          maxX,
          minY,
          maxY
        }
      }
      
      const textBounds = calculateTextBounds()
      const basePanRangeX = textBounds.width
      const basePanRangeY = textBounds.height
      
      // Dynamic pan constraints based on zoom level and text bounds
      const zoomMultiplier = Math.max(1, zoom)
      const panRangeX = basePanRangeX * zoomMultiplier
      const panRangeY = basePanRangeY * zoomMultiplier
      
      const maxPanX = panRangeX
      const maxPanY = panRangeY
      const minPanX = -panRangeX
      const minPanY = -panRangeY
      
      setPan({
        x: Math.max(minPanX, Math.min(maxPanX, newPanX)),
        y: Math.max(minPanY, Math.min(maxPanY, newPanY))
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const resetView = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

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
      className={`relative bg-black text-white h-full flex flex-col ${className}`}
    >
      {/* Page Header */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-700 border-b border-gray-600 flex-shrink-0">
        {/* Top Row - Title and Stats */}
        <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center px-4 py-3 space-y-2 lg:space-y-0">
          <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
            <h3 className="text-xl font-bold text-white">OCR Page {pageData.pageNumber + 1}</h3>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <span className="text-gray-300">{pageData.totalWords || 0} words</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-gray-300">{pageData.totalLines || 0} lines</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                <span className="text-gray-300">{((pageData.confidenceScore || 0) * 100).toFixed(1)}% confidence</span>
              </div>
            </div>
          </div>
          
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <div className="text-sm text-gray-400">
              Pan: <span className="text-blue-300 font-mono">({Math.round(pan.x)}, {Math.round(pan.y)})</span>
            </div>
            <div className="text-sm text-gray-400">
              Zoom: <span className="text-purple-300 font-mono">{Math.round(zoom * 100)}%</span>
            </div>
          </div>
        </div>

        {/* Control Row */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between px-4 py-3 bg-gray-750 border-t border-gray-600 space-y-3 lg:space-y-0">
          {/* Left Controls - View Mode */}
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium text-gray-300">View:</span>
            <div className="flex bg-gray-600 rounded-lg p-1">
              <button
                onClick={() => setViewMode('raw')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-200 ${
                  viewMode === 'raw' 
                    ? 'bg-blue-600 text-white shadow-sm' 
                    : 'text-gray-300 hover:text-white hover:bg-gray-500'
                }`}
              >
                Raw Text
              </button>
              <button
                onClick={() => setViewMode('full')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-200 ${
                  viewMode === 'full' 
                    ? 'bg-blue-600 text-white shadow-sm' 
                    : 'text-gray-300 hover:text-white hover:bg-gray-500'
                }`}
              >
                Full Text
              </button>
            </div>
          </div>

          {/* Center Controls - Display Mode */}
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium text-gray-300">Display:</span>
            <select
              value={displayMode}
              onChange={(e) => setDisplayMode(e.target.value as 'words' | 'lines')}
              className="px-3 py-1.5 bg-gray-600 text-gray-300 hover:bg-gray-500 rounded-md text-sm border border-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
            >
              <option value="words">Words</option>
              <option value="lines">Lines</option>
            </select>
          </div>

          {/* Right Controls - Zoom */}
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium text-gray-300">Zoom:</span>
            <div className="flex items-center bg-gray-600 rounded-lg p-1">
              <button
                onClick={() => handleZoom(-0.2)}
                className="px-2 py-1.5 text-gray-300 hover:text-white hover:bg-gray-500 rounded-md text-sm font-medium transition-all duration-200"
                title="Zoom Out"
              >
                −
              </button>
              <div className="px-3 py-1.5 text-sm text-gray-300 min-w-[50px] text-center">
                {Math.round(zoom * 100)}%
              </div>
              <button
                onClick={() => handleZoom(0.2)}
                className="px-2 py-1.5 text-gray-300 hover:text-white hover:bg-gray-500 rounded-md text-sm font-medium transition-all duration-200"
                title="Zoom In"
              >
                +
              </button>
            </div>
            <button
              onClick={resetView}
              className="px-3 py-1.5 bg-gray-600 text-gray-300 hover:bg-gray-500 rounded-md text-sm font-medium transition-all duration-200 border border-gray-500"
              title="Reset View"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Content based on view mode */}
      {viewMode === 'raw' ? (
        /* Raw Text - Scaled and positioned text blocks with zoom/pan */
        <div 
          ref={canvasRef}
          className="flex-1 overflow-hidden relative cursor-grab active:cursor-grabbing select-none"
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          style={{
            userSelect: 'none',
            WebkitUserSelect: 'none',
            MozUserSelect: 'none',
            msUserSelect: 'none'
          }}
        >
            <div 
              className="relative h-full"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                transformOrigin: '0 0',
                transition: isDragging ? 'none' : 'transform 0.1s ease-out'
              }}
            >
          <div className="relative">
            {/* Word Overlays */}
            {displayMode === 'words' && pageData.wordsData?.map(word => 
              createWordTextBlock(word, handleTextClick, 1, 1)
            )}

            {/* Line Overlays */}
            {displayMode === 'lines' && pageData.linesData?.map(line => 
              createLineTextBlock(line, handleTextClick, 1, 1)
            )}
          </div>
          </div>
        </div>
      ) : (
        /* Full Text - Plain text in a single paragraph with scrolling */
        <div className="flex-1 min-h-0 overflow-y-auto bg-gray-900 overscroll-contain">
          <div className="p-4">
            <pre className="text-gray-100 leading-relaxed whitespace-pre-wrap font-sans">
            {pageData.fullText || 'No text available'}
            </pre>
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
