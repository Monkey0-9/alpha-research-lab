/**
 * Zustand Global State Store for QuantAlpha Workstation
 */

import { create } from 'zustand';

export interface StationState {
  selectedUniverse: string;
  startDate: string;
  endDate: string;
  executionMode: 'PAPER' | 'BACKTEST' | 'LIVE';
  autoRefresh: boolean;
  activeStrategy: string;
  ensembleWeights: {
    lightgbm: number;
    xgboost: number;
    ridge: number;
    mlp: number;
  };
  acknowledgedAlerts: string[];
  
  // Actions
  setUniverse: (u: string) => void;
  setDateRange: (start: string, end: string) => void;
  setExecutionMode: (mode: 'PAPER' | 'BACKTEST' | 'LIVE') => void;
  toggleAutoRefresh: () => void;
  setActiveStrategy: (strat: string) => void;
  setEnsembleWeight: (model: 'lightgbm' | 'xgboost' | 'ridge' | 'mlp', weight: number) => void;
  acknowledgeAlert: (id: string) => void;
}

export const useStationStore = create<StationState>((set) => ({
  selectedUniverse: 'sp500',
  startDate: '2020-01-01',
  endDate: '2024-12-31',
  executionMode: 'PAPER',
  autoRefresh: true,
  activeStrategy: 'Alpha-Ensemble-V4',
  ensembleWeights: {
    lightgbm: 0.40,
    xgboost: 0.30,
    ridge: 0.15,
    mlp: 0.15
  },
  acknowledgedAlerts: [],

  setUniverse: (u) => set({ selectedUniverse: u }),
  setDateRange: (start, end) => set({ startDate: start, endDate: end }),
  setExecutionMode: (mode) => set({ executionMode: mode }),
  toggleAutoRefresh: () => set((s) => ({ autoRefresh: !s.autoRefresh })),
  setActiveStrategy: (strat) => set({ activeStrategy: strat }),
  setEnsembleWeight: (model, weight) =>
    set((s) => ({
      ensembleWeights: {
        ...s.ensembleWeights,
        [model]: weight
      }
    })),
  acknowledgeAlert: (id) =>
    set((s) => ({
      acknowledgedAlerts: [...s.acknowledgedAlerts, id]
    }))
}));
