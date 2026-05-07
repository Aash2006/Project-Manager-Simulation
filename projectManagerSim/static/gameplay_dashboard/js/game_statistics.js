document.addEventListener('DOMContentLoaded', function () {
  const raw = window.dailyStatsData || [];

  if (!raw.length) {
    document.querySelectorAll('.chart-empty').forEach(el => el.classList.remove('d-none'));
    return;
  }

  const labels        = raw.map(d => 'Day ' + d.day);
  const progressData  = raw.map(d => d.progress_gained  ?? 0);
  const scoreData     = raw.map(d => d.score_gained     ?? 0);
  const failData      = raw.map(d => d.tasks_failed     ?? 0);
  const completedData = raw.map(d => d.tasks_completed  ?? 0);

  // Cumulative score
  const cumulativeScore = scoreData.reduce((acc, val, i) => {
    acc.push((acc[i - 1] ?? 0) + val);
    return acc;
  }, []);

  let activeChart = null;

  function destroyActive() {
    if (activeChart) {
      activeChart.destroy();
      activeChart = null;
    }
  }

  function buildProgressChart() {
    destroyActive();
    const ctx = document.getElementById('chartCanvas').getContext('2d');
    activeChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Progress Gained',
          data: progressData,
          backgroundColor: 'rgba(13, 110, 253, 0.3)',
          borderColor: 'rgba(13, 110, 253, 0.9)',
          borderWidth: 1,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: { mode: 'index', intersect: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Progress Points' },
          },
          x: { ticks: { maxRotation: 45 } },
        },
      },
    });
  }

  function buildScoreChart() {
    destroyActive();
    const ctx = document.getElementById('chartCanvas').getContext('2d');
    activeChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Cumulative Score',
            data: cumulativeScore,
            borderColor: 'rgba(25, 135, 84, 0.9)',
            backgroundColor: 'rgba(25, 135, 84, 0.1)',
            borderWidth: 2,
            pointRadius: 3,
            tension: 0.3,
            fill: true,
          },
          {
            label: 'Score This Day',
            data: scoreData,
            borderColor: 'rgba(13, 110, 253, 0.7)',
            backgroundColor: 'transparent',
            borderWidth: 1,
            pointRadius: 2,
            borderDash: [4, 4],
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: { mode: 'index', intersect: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Score' },
          },
          x: { ticks: { maxRotation: 45 } },
        },
      },
    });
  }

  function buildTasksChart() {
    destroyActive();
    const ctx = document.getElementById('chartCanvas').getContext('2d');
    activeChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Completed',
            data: completedData,
            backgroundColor: 'rgba(25, 135, 84, 0.6)',
            borderColor: 'rgba(25, 135, 84, 0.9)',
            borderWidth: 1,
          },
          {
            label: 'Failed',
            data: failData,
            backgroundColor: 'rgba(220, 53, 69, 0.6)',
            borderColor: 'rgba(220, 53, 69, 0.9)',
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: { mode: 'index', intersect: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Tasks' },
            ticks: { stepSize: 1 },
          },
          x: { ticks: { maxRotation: 45 } },
        },
      },
    });
  }

  // Tab switching
  const tabMap = {
    'tab-progress': buildProgressChart,
    'tab-score':    buildScoreChart,
    'tab-tasks':    buildTasksChart,
  };

  document.querySelectorAll('.chart-tab').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.chart-tab').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      tabMap[this.id]?.();
    });
  });

  // Default: load progress tab
  buildProgressChart();
});