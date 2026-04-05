import { Activity } from 'lucide-react'

interface Observation {
  last_reward: number
  cumulative_reward: number
}

interface Props {
  observation: Observation | null
}

export default function RewardLog({ observation }: Props) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-4 h-4 text-emerald-600" />
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Reward Log</h3>
      </div>

      {!observation ? (
        <div className="text-xs text-gray-400 font-mono">
          Waiting for actions...
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Last Reward</span>
            <span className={`font-mono font-bold text-base ${
              observation.last_reward > 0 ? 'text-emerald-600' :
              observation.last_reward < 0 ? 'text-red-500' :
              'text-gray-400'
            }`}>
              {observation.last_reward > 0 ? '+' : ''}{observation.last_reward.toFixed(2)}
            </span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Cumulative</span>
            <span className="font-mono font-bold text-base text-emerald-600">
              {observation.cumulative_reward.toFixed(2)}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
