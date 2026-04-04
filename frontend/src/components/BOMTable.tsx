import { Filter } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

interface BOMRow {
  row_id: number
  vendor_name: string
  part_number: string
  value: string
  package: string
  quantity: number
  status: string
  merged_into: number | null
}

interface Observation {
  rows: BOMRow[]
  task_description: string
}

interface Props {
  observation: Observation | null
}

export default function BOMTable({ observation }: Props) {
  const [filter, setFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  if (!observation) {
    return (
      <div className="p-8 text-center text-gray-400">
        <p>No episode loaded. Click "Reset Episode" to start.</p>
      </div>
    )
  }

  const filteredRows = observation.rows.filter(row => {
    const matchesSearch = filter === '' || 
      row.vendor_name.toLowerCase().includes(filter.toLowerCase()) ||
      row.part_number.toLowerCase().includes(filter.toLowerCase())
    
    const matchesStatus = statusFilter === 'all' || row.status === statusFilter

    return matchesSearch && matchesStatus
  })

  return (
    <div>
      {/* Filters */}
      <div className="p-4 border-b border-navy-700 flex gap-4">
        <div className="flex-1 relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Filter rows... (vendor, part, value)"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-navy-700 border border-navy-600 rounded text-sm focus:outline-none focus:border-emerald-500"
          />
        </div>
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-navy-700 border border-navy-600 rounded text-sm focus:outline-none focus:border-emerald-500"
        >
          <option value="all">All Status</option>
          <option value="raw">RAW</option>
          <option value="normalized">NORMALIZED</option>
          <option value="flagged">FLAGGED</option>
          <option value="merged">MERGED</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-navy-700 text-xs uppercase text-gray-400">
            <tr>
              <th className="px-4 py-3 text-left">#</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Vendor Name</th>
              <th className="px-4 py-3 text-left">Part Number</th>
              <th className="px-4 py-3 text-left">Value</th>
              <th className="px-4 py-3 text-left">Package</th>
              <th className="px-4 py-3 text-right">QTY</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-navy-700">
            {filteredRows.map((row) => (
              <tr
                key={row.row_id}
                className={clsx(
                  'hover:bg-navy-700/50 transition-colors',
                  row.status === 'merged' && 'opacity-50'
                )}
              >
                <td className="px-4 py-3 text-sm text-gray-400">{row.row_id}</td>
                <td className="px-4 py-3">
                  <span className={clsx(
                    'px-2 py-1 rounded text-xs font-medium uppercase',
                    row.status === 'raw' && 'bg-gray-700 text-gray-300',
                    row.status === 'normalized' && 'bg-emerald-700 text-emerald-200',
                    row.status === 'flagged' && 'bg-yellow-700 text-yellow-200',
                    row.status === 'merged' && 'bg-blue-700 text-blue-200'
                  )}>
                    {row.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">{row.vendor_name}</td>
                <td className="px-4 py-3 text-sm font-mono text-emerald-400">{row.part_number}</td>
                <td className="px-4 py-3 text-sm font-mono">{row.value}</td>
                <td className="px-4 py-3 text-sm font-mono text-blue-400">{row.package}</td>
                <td className="px-4 py-3 text-sm text-right">{row.quantity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredRows.length === 0 && (
        <div className="p-8 text-center text-gray-400">
          <p>No rows match the current filters.</p>
        </div>
      )}
    </div>
  )
}
