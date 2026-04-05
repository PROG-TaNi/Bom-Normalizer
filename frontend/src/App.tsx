import { useState, useEffect, useRef } from 'react'
import { Activity, Database, TrendingUp, Upload, Zap, Download } from 'lucide-react'
import axios from 'axios'
import './App.css'
import BOMTable from './components/BOMTable'
import ActionBuilder from './components/ActionBuilder'
import EpisodeStats from './components/EpisodeStats'
import RewardLog from './components/RewardLog'

const API_BASE = '/api'

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
  task_id: string
  task_description: string
  rows: BOMRow[]
  step_count: number
  max_steps: number
  fields_remaining: number
  last_reward: number
  cumulative_reward: number
  done: boolean
}

function App() {
  const [taskId, setTaskId] = useState<'easy' | 'medium' | 'hard'>('easy')
  const [observation, setObservation] = useState<Observation | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLive, setIsLive] = useState(false)
  const [autoNormalizing, setAutoNormalizing] = useState(false)
  const [autoNormalizeProgress, setAutoNormalizeProgress] = useState('')
  const [autoNormalizePercentage, setAutoNormalizePercentage] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const resetEnvironment = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.post(`${API_BASE}/reset?task_id=${taskId}`)
      setObservation(response.data)
      setIsLive(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset environment')
    } finally {
      setLoading(false)
    }
  }

  const sendAction = async (action: any) => {
    if (!observation) return
    
    setLoading(true)
    setError(null)
    try {
      const response = await axios.post(`${API_BASE}/step?task_id=${taskId}`, action)
      setObservation(response.data.observation)
      
      if (response.data.done) {
        setIsLive(false)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute action')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setLoading(true)
    setError(null)
    
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${API_BASE}/upload-bom?task_id=${taskId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setObservation(response.data)
      setIsLive(true)
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setError(detail ? `Upload failed: ${detail}` : 'Upload failed. Make sure the file is a valid .xlsx or .csv.')
    } finally {
      setLoading(false)
      // Reset file input so the same file can be re-selected after a fix
      event.target.value = ''
    }
  }

  const autoNormalizeWithAI = async () => {
    if (!observation) return

    setAutoNormalizing(true)
    setError(null)
    setAutoNormalizeProgress('🤖 Starting AI normalization (this may take 1-2 minutes)...')
    setAutoNormalizePercentage(10)

    try {
      // Increase timeout to 5 minutes for LLM processing
      const response = await axios.post(`${API_BASE}/auto-normalize?task_id=${taskId}`, {}, {
        timeout: 300000  // 5 minutes
      })
      
      if (response.data.success) {
        setAutoNormalizePercentage(90)
        setAutoNormalizeProgress(`✅ Completed ${response.data.steps} normalization steps`)
        
        // Update with final observation
        setObservation(response.data.final_observation)
        setAutoNormalizePercentage(100)
        
        if (response.data.final_observation.done) {
          setIsLive(false)
          setAutoNormalizeProgress('✅ AI normalization complete! Ready to download.')
        } else {
          setAutoNormalizeProgress(`✅ Normalized ${response.data.steps} fields. ${response.data.final_observation.fields_remaining} remaining.`)
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to auto-normalize')
      setAutoNormalizeProgress('❌ Normalization failed')
      setAutoNormalizePercentage(0)
    } finally {
      setAutoNormalizing(false)
    }
  }

  const downloadNormalizedBOM = () => {
    if (!observation) return

    const csvContent = [
      ['Vendor', 'Part Number', 'Value', 'Package', 'Quantity'].join(','),
      ...observation.rows
        .filter(row => row.status !== 'merged')
        .map(row => [
          row.vendor_name,
          row.part_number,
          row.value,
          row.package,
          row.quantity
        ].join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `normalized_bom_${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  useEffect(() => {
    // Check health on mount
    axios.get(`${API_BASE}/health`)
      .then(() => console.log('API connected'))
      .catch(() => setError('Cannot connect to API'))
  }, [])

  return (
    <div className="min-h-screen bg-slate-100 text-gray-900">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="w-6 h-6 text-emerald-600" />
            <h1 className="text-xl font-bold text-gray-800">BOM Normalizer</h1>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              <button
                onClick={() => setTaskId('easy')}
                className={`px-4 py-2 rounded font-medium text-sm ${
                  taskId === 'easy'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                EASY
              </button>
              <button
                onClick={() => setTaskId('medium')}
                className={`px-4 py-2 rounded font-medium text-sm ${
                  taskId === 'medium'
                    ? 'bg-amber-500 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                MEDIUM
              </button>
              <button
                onClick={() => setTaskId('hard')}
                className={`px-4 py-2 rounded font-medium text-sm ${
                  taskId === 'hard'
                    ? 'bg-red-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                HARD
              </button>
            </div>
            
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-emerald-500' : 'bg-gray-400'}`} />
              <span className="text-sm text-gray-500">
                {isLive ? 'Live' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="p-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Left Column - Stats & Actions */}
          <div className="col-span-3 space-y-6">
            <EpisodeStats observation={observation} />
            <ActionBuilder onSendAction={sendAction} disabled={loading || !observation || observation.done} />
            <RewardLog observation={observation} />
          </div>

          {/* Right Column - BOM Table */}
          <div className="col-span-9">
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-emerald-600" />
                    <h2 className="text-lg font-semibold text-gray-800">ENVIRONMENT</h2>
                  </div>
                  
                  <div className="flex gap-2">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={loading || autoNormalizing}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded text-sm font-medium transition-colors flex items-center gap-2"
                    >
                      <Upload className="w-4 h-4" />
                      Upload Excel
                    </button>
                    <a
                      href={`${API_BASE}/download-template`}
                      download="bom_template.xlsx"
                      className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-gray-700 border border-gray-300 rounded text-sm font-medium transition-colors flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Template
                    </a>
                    
                    <button
                      onClick={resetEnvironment}
                      disabled={loading || autoNormalizing}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 text-white rounded text-sm font-medium transition-colors"
                    >
                      {loading ? 'Loading...' : 'Reset Episode'}
                    </button>
                  </div>
                </div>

                {/* AI Auto-Normalize Section */}
                {observation && (
                  <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-semibold text-emerald-700 mb-1">⚡ AI Auto-Normalize</h3>
                        <p className="text-xs text-gray-500">
                          Let AI automatically normalize all rows using LLM intelligence
                        </p>
                      </div>
                      
                      <div className="flex gap-2">
                        <button
                          onClick={autoNormalizeWithAI}
                          disabled={autoNormalizing || loading}
                          className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-lg text-sm font-bold transition-all flex items-center gap-2 shadow-sm"
                        >
                          <Zap className="w-5 h-5" />
                          {autoNormalizing ? 'AI Working...' : 'Auto-Normalize with AI'}
                        </button>
                        
                        <button
                          onClick={downloadNormalizedBOM}
                          className="px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                        >
                          <Download className="w-4 h-4" />
                          Download BOM
                        </button>
                      </div>
                    </div>
                    
                    {autoNormalizing && (
                      <div className="mt-3">
                        <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                          <div 
                            className="bg-gradient-to-r from-emerald-600 to-emerald-400 h-3 rounded-full transition-all duration-300 flex items-center justify-center"
                            style={{ width: `${autoNormalizePercentage}%` }}
                          >
                            <span className="text-xs font-bold text-white">{autoNormalizePercentage}%</span>
                          </div>
                        </div>
                        <div className="text-xs text-emerald-700 bg-emerald-100 rounded px-3 py-2">
                          {autoNormalizeProgress}
                        </div>
                      </div>
                    )}
                    
                    {!autoNormalizing && autoNormalizeProgress && (
                      <div className="mt-3 text-xs text-emerald-700 bg-emerald-100 rounded px-3 py-2">
                        {autoNormalizeProgress}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {error && (() => {
                // Parse structured upload errors into sections
                const missingMatch = error.match(/Missing required columns:\s*(\[[^\]]+\])/)
                const foundMatch   = error.match(/Your file has:\s*(\[[^\]]+\])/)
                const isMissingCols = missingMatch && foundMatch

                const parseList = (raw: string) =>
                  raw.replace(/[\[\]']/g, '').split(',').map(s => s.trim()).filter(Boolean)

                return isMissingCols ? (
                  <div className="mx-4 mt-4 rounded-lg border border-red-200 bg-red-50 overflow-hidden text-sm">
                    {/* Header */}
                    <div className="flex items-center gap-2 px-4 py-3 bg-red-100 border-b border-red-200">
                      <svg className="w-4 h-4 text-red-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                      </svg>
                      <span className="font-semibold text-red-700">Wrong file — column names don't match</span>
                      <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600 text-lg leading-none">&times;</button>
                    </div>

                    <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Missing */}
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-red-500 mb-2">Required columns (missing)</p>
                        <div className="flex flex-wrap gap-1">
                          {parseList(missingMatch[1]).map(col => (
                            <span key={col} className="px-2 py-0.5 rounded bg-red-200 text-red-800 font-mono text-xs">{col}</span>
                          ))}
                        </div>
                      </div>

                      {/* Found */}
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">Columns in your file</p>
                        <div className="flex flex-wrap gap-1 max-h-28 overflow-y-auto">
                          {parseList(foundMatch[1]).map(col => (
                            <span key={col} className="px-2 py-0.5 rounded bg-gray-200 text-gray-700 font-mono text-xs">{col}</span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Footer tip */}
                    <div className="px-4 py-2 bg-amber-50 border-t border-amber-100 text-amber-700 text-xs flex items-center gap-2">
                      <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20A10 10 0 0012 2z" />
                      </svg>
                      Click the <strong className="mx-1">Template</strong> button above to download a correctly-formatted Excel file.
                    </div>
                  </div>
                ) : (
                  <div className="mx-4 mt-4 flex items-start gap-3 p-4 rounded-lg border border-red-200 bg-red-50 text-red-700 text-sm">
                    <svg className="w-4 h-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="flex-1">{error}</span>
                    <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 text-lg leading-none">&times;</button>
                  </div>
                )
              })()}

              <BOMTable observation={observation} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
