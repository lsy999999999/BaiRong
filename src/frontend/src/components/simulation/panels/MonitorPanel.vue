<template>
  <div class="monitor-panel">
    <h2>Simulation Monitor</h2>
    <div class="panel-content">
      <div class="charts-container">
        <div class="chart-row" v-for="(row, rowIndex) in chartRows" :key="rowIndex">
          <div v-for="(item) in row" :key="item.name" class="chart-item">
            <div class="chart-header">
              <h3>{{ item.name }}</h3>
              <p class="chart-description">{{ metrics[item.name]?.description }}</p>
            </div>
            <div class="chart-body" :ref="el => setChartRef(item.name, el)"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import axios from 'axios';

export default {
  name: 'MonitorPanel',
  data() {
    return {
      metrics: {},
      chartRefs: {},
      charts: []
    };
  },
  computed: {
    chartRows() {
      const items = Object.entries(this.metrics).map(([key, value]) => ({
        name: value.name || key,
        data: value.data,
        type: value.visualization_type || 'line'
      }));
      const rows = [];
      for (let i = 0; i < items.length; i += 2) {
        rows.push(items.slice(i, i + 2));
      }
      return rows;
    }
  },
  mounted() {
    this.updateInterval = setInterval(this.refreshChartData, 5000);
    const observer = new MutationObserver(() => {
      this.renderCharts();
    });
    const layout = document.querySelector('.simulation-layout');
    if (layout) {
      observer.observe(layout, { attributes: true, attributeFilter: ['class'] });
    }
    this._themeObserver = observer;
    this.getEcharts();
    window.addEventListener('resize', this.resizeCharts);
  },
  beforeUnmount() {
    clearInterval(this.updateInterval);
    if (this._themeObserver) {
      this._themeObserver.disconnect();
    }
    window.removeEventListener('resize', this.resizeCharts);
    this.charts.forEach(chart => chart.dispose());
  },
  methods: {
    generateChartOption(metric) {
      const isDark = document.querySelector('.simulation-layout')?.classList.contains('dark-theme');
      const textColor = isDark ? '#ddd' : '#333';
      const axisColor = isDark ? '#888' : '#ccc';

      if (metric.visualization_type === 'pie') {
        return {
          tooltip: { trigger: 'item' },
          legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: { color: textColor, fontSize: 12 }
          },
          series: metric.data.series.map(s => ({
            ...s,
            label: { color: textColor, fontSize: 12 },
            labelLine: { lineStyle: { color: textColor } }
          }))
        };
      } else {
        return {
          tooltip: { trigger: 'axis' },
          legend: {
            bottom: 10,
            textStyle: { color: textColor },
            ...(metric.data.legend || {})
          },
          grid: metric.data.grid || { top:'3%', left: '3%', right: '4%', bottom: '15%', containLabel: true },
          xAxis: {
            type: metric.data?.xAxis?.type || 'category',
            data: metric.data?.xAxis?.data || [],
            axisLine: { lineStyle: { color: axisColor } },
            axisLabel: { 
              color: textColor, 
              fontSize: 12,
              interval: function(index, value) {
                // 计算间隔，确保最多显示4个标签
                const total = metric.data?.xAxis?.data?.length || 0;
                const interval = Math.ceil(total / 4);
                return index % interval === 0;
              },
              rotate: 15  // 标签旋转45度，防止重叠
            },
            ...metric.data.xAxis
          },
          yAxis: {
            type: 'value',
            axisLine: { lineStyle: { color: axisColor } },
            axisLabel: { color: textColor, fontSize: 12 },
            ...metric.data.yAxis
          },
          series: metric.data.series || []
        };
      }
    },
    refreshChartData() {
      axios.get("/api/monitor/" + localStorage.getItem("scenarioName") + "/metrics")
        .then((res) => {
          const newMetrics = res.data.metrics || {};
          for (const [key, metric] of Object.entries(newMetrics)) {
            const chartIndex = this.charts.findIndex((_, i) => Object.values(this.metrics)[i]?.name === key);
            if (chartIndex !== -1 && this.charts[chartIndex]) {
              this.metrics[key].data = metric.data;
              this.charts[chartIndex].setOption({ ...this.generateChartOption(metric) }, true);
            }
          }
        });
    },
    getEcharts() {
      axios.get("/api/monitor/" + localStorage.getItem("scenarioName") + "/metrics")
        .then((res) => {
          this.metrics = res.data.metrics || {};
          this.$nextTick(() => {
            this.renderCharts();
          });
        });
    },
    setChartRef(name, el) {
      if (el) this.chartRefs[name] = el;
    },
    renderCharts() {
      this.charts.forEach(chart => chart.dispose());
      this.charts = [];

      for (const [key, metric] of Object.entries(this.metrics)) {
        const el = this.chartRefs[metric.name || key];
        if (!el || el.clientWidth === 0 || el.clientHeight === 0) continue;

        const chart = echarts.init(el);
        const isDark = document.querySelector('.simulation-layout')?.classList.contains('dark-theme');
        const textColor = isDark ? '#ddd' : '#333';
        const axisColor = isDark ? '#888' : '#ccc';

        let option = {};
        if (metric.visualization_type === 'pie') {
          option = {
            tooltip: { trigger: 'item' },
            legend: {
              orient: 'vertical',
              left: 'left',
              textStyle: {
                color: textColor,
                fontSize: 12
              }
            },
            series: metric.data.series.map(s => ({
              ...s,
              label: { color: textColor, fontSize: 12 },
              labelLine: { lineStyle: { color: textColor } }
            }))
          };
        } else {
          option = {
            tooltip: { trigger: 'axis' },
            legend: {
              bottom: 10,
              textStyle: { color: textColor },
              ...(metric.data.legend || {})
            },
            grid: metric.data.grid || { left: '3%', right: '4%', bottom: '15%', containLabel: true },
            xAxis: {
              type: metric.data?.xAxis?.type || 'category',
              data: metric.data?.xAxis?.data || [],
              axisLine: { lineStyle: { color: axisColor } },
              axisLabel: { 
                color: textColor, 
                fontSize: 12,
                interval: function(index, value) {
                  // 计算间隔，确保最多显示4个标签
                  const total = metric.data?.xAxis?.data?.length || 0;
                  const interval = Math.ceil(total / 4);
                  return index % interval === 0;
                },
                rotate: 15  // 标签旋转45度，防止重叠
              },
              ...metric.data.xAxis
            },
            yAxis: {
              type: 'value',
              axisLine: { lineStyle: { color: axisColor } },
              axisLabel: { color: textColor },
              ...metric.data.yAxis
            },
            series: metric.data.series || []
          };
        }

        chart.setOption(this.generateChartOption(metric));
        this.charts.push(chart);
      }
    },
    resizeCharts() {
      this.$nextTick(() => {
        this.charts.forEach(chart => {
          if (chart && chart.resize) chart.resize();
        });
      });
    }
  }
};
</script>

<style scoped>
.monitor-panel {
  padding: 20px;
  background-color: var(--panel-bg, #ffffff);
  transition: all 0.3s ease;
}

h2 {
  margin-bottom: 20px;
  font-size: 1.5rem;
  color: var(--text-color, #333333);
}

.panel-content {
  min-height: 100px;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  padding: 15px;
  background-color: var(--panel-bg, #f8f8f8);
  transition: all 0.3s ease;
  overflow: auto;
}

.charts-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.chart-row {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.chart-item {
  flex: 1 1 calc(50% - 7.5px);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 6px;
  background-color: var(--card-bg, #ffffff);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 300px;
}

.chart-header {
  padding: 10px 15px;
  border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.chart-header h3 {
  margin: 0;
  font-size: 14px;
  color: var(--text-color, #333333);
}

.chart-body {
  flex: 1;
  padding: 10px;
  min-height: 260px;
}

.simulation-layout.dark-theme .monitor-panel {
  background-color: var(--dark-panel-bg, #1a1a1a);
}

.simulation-layout.dark-theme h2,
.simulation-layout.dark-theme .chart-header h3 {
  color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme .panel-content {
  background-color: var(--dark-panel-bg, #1a1a1a);
  border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme .chart-item {
  background-color: var(--dark-card-bg, #2a2a2a);
  border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme .chart-header {
  border-color: var(--dark-border-color, #333333);
}

@media (max-width: 768px) {
  .chart-row {
    flex-direction: column;
  }

  .chart-item {
    flex: 1 1 100%;
  }

  .chart-body {
    min-height: 200px;
  }
}

.chart-description {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary-color, #666);
}

.simulation-layout.dark-theme .chart-description {
  color: var(--dark-text-secondary-color, #aaa);
}
</style>
