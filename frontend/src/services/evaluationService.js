import apiClient from './api';

export const evaluationService = {
  /**
   * Fetch measured offline model evaluation metrics (precision, recall, F1, cohort breakdown).
   */
  async getSummary() {
    return apiClient.get('/evaluation/summary');
  },

  /**
   * Fetch verification status of the 5 mandatory assignment edge cases.
   */
  async getEdgeCases() {
    return apiClient.get('/evaluation/edge-cases');
  },

  /**
   * Fetch complete data integrity validation audit.
   */
  async getDataValidation() {
    return apiClient.get('/evaluation/data-validation');
  },
};

export default evaluationService;
