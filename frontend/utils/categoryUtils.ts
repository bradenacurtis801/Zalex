/**
 * Utility functions for category-related operations
 */

/**
 * Get a consistent color scheme for a category based on its name
 * @param category - The category name
 * @returns Tailwind CSS classes for the category color scheme
 */
export const getCategoryColor = (category: string): string => {
  // Predefined color schemes for consistent category colors
  const colorSchemes = [
    'bg-blue-100 text-blue-800 border-blue-200',
    'bg-green-100 text-green-800 border-green-200',
    'bg-purple-100 text-purple-800 border-purple-200',
    'bg-orange-100 text-orange-800 border-orange-200',
    'bg-pink-100 text-pink-800 border-pink-200',
    'bg-indigo-100 text-indigo-800 border-indigo-200',
    'bg-teal-100 text-teal-800 border-teal-200',
    'bg-cyan-100 text-cyan-800 border-cyan-200',
    'bg-amber-100 text-amber-800 border-amber-200',
    'bg-emerald-100 text-emerald-800 border-emerald-200',
    'bg-rose-100 text-rose-800 border-rose-200',
    'bg-violet-100 text-violet-800 border-violet-200',
    'bg-sky-100 text-sky-800 border-sky-200',
    'bg-lime-100 text-lime-800 border-lime-200',
    'bg-fuchsia-100 text-fuchsia-800 border-fuchsia-200',
    'bg-slate-100 text-slate-800 border-slate-200'
  ]
  
  // Simple hash function to convert category name to consistent index
  let hash = 0
  for (let i = 0; i < category.length; i++) {
    const char = category.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32-bit integer
  }
  
  // Use absolute value and modulo to get index within color schemes array
  const colorIndex = Math.abs(hash) % colorSchemes.length
  return colorSchemes[colorIndex]
}

/**
 * Get a human-readable label for a category
 * @param category - The category name
 * @returns Capitalized category label
 */
export const getCategoryLabel = (category: string): string => {
  switch (category) {
    case 'personas':
      return 'Personas'
    case 'mercantil':
      return 'Mercantil'
    case 'inmuebles':
      return 'Inmuebles'
    case 'other':
      return 'Other'
    default:
      return category.charAt(0).toUpperCase() + category.slice(1)
  }
}
