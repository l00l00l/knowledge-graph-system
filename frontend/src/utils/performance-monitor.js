// utils/performance-monitor.js

export class PerformanceMonitor {
    constructor() {
      this.metrics = {
        renderTime: [],
        queryTime: [],
        dataLoadTime: []
      };
      this.marks = {};
    }
    
    startMark(name) {
      this.marks[name] = performance.now();
    }
    
    endMark(name, category) {
      if (!this.marks[name]) {
        console.warn(`No start mark found for ${name}`);
        return;
      }
      
      const duration = performance.now() - this.marks[name];
      delete this.marks[name];
      
      if (category && this.metrics[category]) {
        this.metrics[category].push({
          name,
          duration,
          timestamp: new Date()
        });
      }
      
      return duration;
    }
    
    logMetric(category, name, duration) {
      if (this.metrics[category]) {
        this.metrics[category].push({
          name,
          duration,
          timestamp: new Date()
        });
      }
    }
    
    getAverageMetrics() {
      const result = {};
      
      for (const [category, measurements] of Object.entries(this.metrics)) {
        if (measurements.length > 0) {
          result[category] = {
            average: measurements.reduce((sum, m) => sum + m.duration, 0) / measurements.length,
            max: Math.max(...measurements.map(m => m.duration)),
            min: Math.min(...measurements.map(m => m.duration)),
            count: measurements.length
          };
        }
      }
      
      return result;
    }
    
    identifyBottlenecks() {
      const averages = this.getAverageMetrics();
      const bottlenecks = [];
      
      // 定义性能阈值（毫秒）
      const thresholds = {
        renderTime: 100,
        queryTime: 500,
        dataLoadTime: 1000
      };
      
      for (const [category, metrics] of Object.entries(averages)) {
        if (metrics.average > thresholds[category]) {
          bottlenecks.push({
            category,
            average: metrics.average,
            threshold: thresholds[category],
            severity: (metrics.average / thresholds[category]).toFixed(1)
          });
        }
      }
      
      return bottlenecks.sort((a, b) => b.severity - a.severity);
    }
    
    clearMetrics() {
      for (const category in this.metrics) {
        this.metrics[category] = [];
      }
    }
    
    // 将性能数据发送到服务器
    async reportToServer() {
      try {
        const response = await fetch('/api/performance-metrics', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            metrics: this.metrics,
            userAgent: navigator.userAgent,
            timestamp: new Date(),
            averages: this.getAverageMetrics(),
            bottlenecks: this.identifyBottlenecks()
          })
        });
        
        return await response.json();
      } catch (error) {
        console.error('Failed to report performance metrics:', error);
        return null;
      }
    }
  }
  
  // 创建单例实例
  export const performanceMonitor = new PerformanceMonitor();