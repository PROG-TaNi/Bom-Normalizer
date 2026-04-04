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
    formData.append('task_id', taskId)

    try {
      const response = await axios.post(`${API_BASE}/upload-bom`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setObservation(response.data)
      setIsLive(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload file')
    } finally {
      setLoading(false)
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
    <div className="min-h-screen bg-navy-900 text-white">
      {/* Header */}
      <header className="bg-navy-800 border-b border-navy-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="w-6 h-6 text-emerald-400" />
            <h1 className="text-xl font-bold">BOM Normalizer</h1>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              <button
                onClick={() => setTaskId('easy')}
                className={`px-4 py-2 rounded ${
                  taskId === 'easy'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-navy-700 text-gray-300 hover:bg-navy-600'
                }`}
              >
                EASY
              </button>
              <button
                onClick={() => setTaskId('medium')}
                className={`px-4 py-2 rounded ${
                  taskId === 'medium'
                    ? 'bg-yellow-600 text-white'
                    : 'bg-navy-700 text-gray-300 hover:bg-navy-600'
                }`}
              >
                MEDIUM
              </button>
              <button
                onClick={() => setTaskId('hard')}
                className={`px-4 py-2 rounded ${
                  taskId === 'hard'
                    ? 'bg-red-600 text-white'
                    : 'bg-navy-700 text-gray-300 hover:bg-navy-600'
                }`}
              >
                HARD
              </button>
            </div>
            
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-500' : 'bg-gray-500'}`} />
              <span className="text-sm text-gray-400">
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
            <div className="bg-navy-800 rounded-lg border border-navy-700">
              <div className="p-4 border-b border-navy-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-emerald-400" />
                    <h2 className="text-lg font-semibold">ENVIRONMENT</h2>
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
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded text-sm font-medium transition-colors flex items-center gap-2"
                    >
                      <Upload className="w-4 h-4" />
                      Upload Excel
                    </button>
                    
                    <button
                      onClick={resetEnvironment}
                      disabled={loading || autoNormalizing}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-600 rounded text-sm font-medium transition-colors"
                    >
                      {loading ? 'Loading...' : 'Reset Episode'}
                    </button>
                  </div>
                </div>

                {/* AI Auto-Normalize Section */}
                {observation && (
                  <div className="bg-navy-900 rounded-lg p-4 border border-emerald-600/30">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-semibold text-emerald-400 mb-1">⚡ AI Auto-Normalize</h3>
                        <p className="text-xs text-gray-400">
                          Let AI automatically normalize all rows using LLM intelligence
                        </p>
                      </div>
                      
                      <div className="flex gap-2">
                        <button
                          onClick={autoNormalizeWithAI}
                          disabled={autoNormalizing || loading}
                          className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 disabled:from-gray-600 disabled:to-gray-600 rounded-lg text-sm font-bold transition-all flex items-center gap-2 shadow-lg"
                        >
                          <Zap className="w-5 h-5" />
                          {autoNormalizing ? 'AI Working...' : 'Auto-Normalize with AI'}
                        </button>
                        
                        <button
                          onClick={downloadNormalizedBOM}
                          className="px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                        >
                          <Download className="w-4 h-4" />
                          Download BOM
                        </button>
                      </div>
                    </div>
                    
                    {autoNormalizing && (
                      <div className="mt-3">
                        {/* Progress Bar */}
                        <div className="w-full bg-navy-800 rounded-full h-3 mb-2">
                          <div 
                            className="bg-gradient-to-r from-emerald-600 to-emerald-400 h-3 rounded-full transition-all duration-300 flex items-center justify-center"
                            style={{ width: `${autoNormalizePercentage}%` }}
                          >
                            <span className="text-xs font-bold text-white">{autoNormalizePercentage}%</span>
                          </div>
                        </div>
                        {/* Progress Message */}
                        <div className="text-xs text-emerald-300 bg-emerald-900/20 rounded px-3 py-2">
                          {autoNormalizeProgress}
                        </div>
                      </div>
                    )}
                    
                    {!autoNormalizing && autoNormalizeProgress && (
                      <div className="mt-3 text-xs text-emerald-300 bg-emerald-900/20 rounded px-3 py-2">
                        {autoNormalizeProgress}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {error && (
                <div className="p-4 bg-red-900/20 border-b border-red-800 text-red-400">
                  {error}
                </div>
              )}

              <BOMTable observation={observation} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
