import { Send } from 'lucide-react'
import { useState } from 'react'

interface Props {
  onSendAction: (action: any) => void
  disabled: boolean
}

export default function ActionBuilder({ onSendAction, disabled }: Props) {
  const [actionType, setActionType] = useState('normalize_vendor')
  const [rowId, setRowId] = useState('')
  const [newValue, setNewValue] = useState('')
  const [duplicateRowId, setDuplicateRowId] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const action: any = {
      action_type: actionType
    }

    if (actionType !== 'submit') {
      action.row_id = parseInt(rowId)
    }

    if (actionType === 'merge_rows') {
      action.duplicate_row_id = parseInt(duplicateRowId)
    } else if (actionType !== 'submit' && actionType !== 'flag_anomaly') {
      action.new_value = newValue
    }

    onSendAction(action)

    // Reset form
    setRowId('')
    setNewValue('')
    setDuplicateRowId('')
  }

  const needsRowId = actionType !== 'submit'
  const needsNewValue = ['normalize_vendor', 'normalize_value', 'normalize_package', 'normalize_part'].includes(actionType)
  const needsDuplicateId = actionType === 'merge_rows'

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
      <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4 tracking-wide">Action Builder</h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Action Type */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-2">ACTION TYPE</label>
          <select
            value={actionType}
            onChange={(e) => setActionType(e.target.value)}
            className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            disabled={disabled}
          >
            <option value="normalize_vendor">normalize_vendor</option>
            <option value="normalize_value">normalize_value</option>
            <option value="normalize_package">normalize_package</option>
            <option value="normalize_part">normalize_part</option>
            <option value="merge_rows">merge_rows</option>
            <option value="flag_anomaly">flag_anomaly</option>
            <option value="submit">submit</option>
          </select>
        </div>

        {/* Row ID */}
        {needsRowId && (
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-2">ROW ID</label>
            <input
              type="number"
              value={rowId}
              onChange={(e) => setRowId(e.target.value)}
              placeholder="e.g. 1"
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              disabled={disabled}
              required
            />
          </div>
        )}

        {/* New Value */}
        {needsNewValue && (
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-2">NEW VALUE</label>
            <input
              type="text"
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              placeholder="e.g. Texas Instruments"
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              disabled={disabled}
              required
            />
          </div>
        )}

        {/* Duplicate Row ID */}
        {needsDuplicateId && (
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-2">DUPLICATE ROW ID</label>
            <input
              type="number"
              value={duplicateRowId}
              onChange={(e) => setDuplicateRowId(e.target.value)}
              placeholder="e.g. 5"
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              disabled={disabled}
              required
            />
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={disabled}
          className="w-full px-4 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-200 disabled:text-gray-400 text-white rounded font-medium transition-colors flex items-center justify-center gap-2 shadow-sm"
        >
          <Send className="w-4 h-4" />
          Send action →
        </button>
      </form>

      {/* API Request Log */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2 tracking-wide">API REQUEST LOG</h4>
        <div className="text-xs text-gray-400 font-mono">
          No requests yet. Press Reset to begin.
        </div>
      </div>
    </div>
  )
}
