import api from './api'
import type { OptimizeRequest, StrategyRequest, OptimizationResultOut } from '../types/optimizer'

export const optimizerService = {
  async optimize(req: OptimizeRequest): Promise<OptimizationResultOut> {
    const res = await api.post<OptimizationResultOut>('/optimizer/optimize', req)
    return res.data
  },

  async strategy(req: StrategyRequest): Promise<OptimizationResultOut> {
    const res = await api.post<OptimizationResultOut>('/optimizer/strategy', req)
    return res.data
  },
}
