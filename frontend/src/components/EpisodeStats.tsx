import { TrendingUp, Target, Zap } from 'lucide-react'

interface Observation {
  task_id: string
  step_count: number
  max_steps: number
  fields_remaining: number
  cumulative_reward: number
}

interface Props {
  observation: Observation | null
}

export default function EpisodeStats({ observation }: Props) {
  if (!observation) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4 tracking-wide">Episode Stats</h3>
        <div className="text-center text-gray-400 py-8">
          No episode loaded
        </div>
      </div>
    )
  }

  const progress = (observation.step_count / observation.max_steps) * 100

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
      <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4 tracking-wide">Episode Stats</h3>
      
      <div className="space-y-5">
        {/* Steps */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-blue-500" />
              <span className="text-sm text-gray-500">Steps Taken</span>
            </div>
            <span className="text-2xl font-bold text-gray-800">{observation.step_count}</span>
          </div>
          <div className="text-xs text-gray-400 mb-2">
            {observation.max_steps} steps budget
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Cumulative Reward */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-600" />
            <span className="text-sm text-gray-500">Cumulative Reward</span>
          </div>
          <span className="text-2xl font-bold text-emerald-600">
            {observation.cumulative_reward.toFixed(2)}
          </span>
        </div>

        {/* Fields Remaining */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-500" />
            <span className="text-sm text-gray-500">Fields Remaining</span>
          </div>
          <span className="text-2xl font-bold text-amber-500">
            {observation.fields_remaining}
          </span>
        </div>
      </div>

      {/* Baseline Scores */}
      <div className="mt-6 pt-5 border-t border-gray-200">
        <h4 className="text-xs font-semibold text-gray-500 uppercase mb-3 tracking-wide">Baseline Scores</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">easy</span>
            <div className="flex items-center gap-2">
              <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full" style={{ width: '85%' }} />
              </div>
              <span className="font-mono text-gray-700 text-xs">0.85</span>
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">medium</span>
            <div className="flex items-center gap-2">
              <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-amber-500 rounded-full" style={{ width: '55%' }} />
              </div>
              <span className="font-mono text-gray-700 text-xs">0.55</span>
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">hard</span>
            <div className="flex items-center gap-2">
              <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-red-500 rounded-full" style={{ width: '25%' }} />
              </div>
              <span className="font-mono text-gray-700 text-xs">0.25</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
