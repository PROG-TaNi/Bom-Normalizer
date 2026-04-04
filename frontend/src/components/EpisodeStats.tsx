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
      <div className="bg-navy-800 rounded-lg border border-navy-700 p-6">
        <h3 className="text-sm font-semibold text-gray-400 uppercase mb-4">Episode Stats</h3>
        <div className="space-y-4">
          <div className="text-center text-gray-500 py-8">
            No episode loaded
          </div>
        </div>
      </div>
    )
  }

  const progress = (observation.step_count / observation.max_steps) * 100

  return (
    <div className="bg-navy-800 rounded-lg border border-navy-700 p-6">
      <h3 className="text-sm font-semibold text-gray-400 uppercase mb-4">Episode Stats</h3>
      
      <div className="space-y-4">
        {/* Steps */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-gray-400">Steps Taken</span>
            </div>
            <span className="text-2xl font-bold">{observation.step_count}</span>
          </div>
          <div className="text-xs text-gray-500">
            {observation.max_steps} steps budget
          </div>
          <div className="mt-2 h-2 bg-navy-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Cumulative Reward */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span className="text-sm text-gray-400">Cumulative Reward</span>
            </div>
            <span className="text-2xl font-bold text-emerald-400">
              {observation.cumulative_reward.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Fields Remaining */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-gray-400">Fields Remaining</span>
            </div>
            <span className="text-2xl font-bold text-yellow-400">
              {observation.fields_remaining}
            </span>
          </div>
        </div>
      </div>

      {/* Baseline Scores */}
      <div className="mt-6 pt-6 border-t border-navy-700">
        <h4 className="text-xs font-semibold text-gray-400 uppercase mb-3">Baseline Scores</h4>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">easy</span>
            <span className="font-mono">0.85</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">medium</span>
            <span className="font-mono">0.55</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">hard</span>
            <span className="font-mono">0.25</span>
          </div>
        </div>
      </div>
    </div>
  )
}
