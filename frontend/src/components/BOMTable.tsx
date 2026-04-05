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
      <div className="p-12 text-center text-gray-400">
        <p className="text-base">No episode loaded. Click <span className="font-semibold text-emerald-600">Reset Episode</span> to start.</p>
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
      <div className="p-4 border-b border-gray-200 flex gap-4">
        <div className="flex-1 relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Filter rows... (vendor, part, value)"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white border border-gray-300 rounded text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
          />
        </div>
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-white border border-gray-300 rounded text-sm text-gray-700 focus:outline-none focus:border-emerald-500"
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
          <thead className="bg-gray-50 text-xs uppercase text-gray-500 border-b border-gray-200">
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
          <tbody className="divide-y divide-gray-100">
            {filteredRows.map((row) => (
              <tr
                key={row.row_id}
                className={clsx(
                  'hover:bg-slate-50 transition-colors',
                  row.status === 'merged' && 'opacity-40'
                )}
              >
                <td className="px-4 py-3 text-sm text-gray-400 font-mono">{row.row_id}</td>
                <td className="px-4 py-3">
                  <span className={clsx(
                    'px-2 py-1 rounded text-xs font-medium uppercase border',
                    row.status === 'raw' && 'bg-gray-100 text-gray-600 border-gray-300',
                    row.status === 'normalized' && 'bg-emerald-50 text-emerald-700 border-emerald-200',
                    row.status === 'flagged' && 'bg-amber-50 text-amber-700 border-amber-200',
                    row.status === 'merged' && 'bg-blue-50 text-blue-700 border-blue-200'
                  )}>
                    {row.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-800 font-medium">{row.vendor_name}</td>
                <td className="px-4 py-3 text-sm font-mono text-emerald-700">{row.part_number}</td>
                <td className="px-4 py-3 text-sm font-mono text-gray-700">{row.value}</td>
                <td className="px-4 py-3 text-sm font-mono text-blue-600">{row.package}</td>
                <td className="px-4 py-3 text-sm text-right text-gray-600">{row.quantity}</td>
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
