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
    <div className="bg-navy-800 rounded-lg border border-navy-700 p-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-4 h-4 text-emerald-400" />
        <h3 className="text-sm font-semibold text-gray-400 uppercase">Reward Log</h3>
      </div>

      {!observation ? (
        <div className="text-xs text-gray-500 font-mono">
          Waiting for actions...
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-400">Last Reward:</span>
            <span className={`font-mono font-bold ${
              observation.last_reward > 0 ? 'text-emerald-400' :
              observation.last_reward < 0 ? 'text-red-400' :
              'text-gray-400'
            }`}>
              {observation.last_reward > 0 ? '+' : ''}{observation.last_reward.toFixed(2)}
            </span>
          </div>
          
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-400">Cumulative:</span>
            <span className="font-mono font-bold text-emerald-400">
              {observation.cumulative_reward.toFixed(2)}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
