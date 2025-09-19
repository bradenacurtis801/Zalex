interface FileListProps {
  files: File[]
  onRemoveFile: (index: number) => void
}

export default function FileList({ files, onRemoveFile }: FileListProps) {
  if (files.length === 0) return null

  return (
    <div className="mt-4 space-y-2">
      {files.map((file, index) => (
        <div key={index} className="flex justify-between items-center bg-gray-100 p-2 rounded">
          <span className="text-sm truncate">{file.name}</span>
          <button
            type="button"
            onClick={() => onRemoveFile(index)}
            className="text-red-500 hover:text-red-700"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
