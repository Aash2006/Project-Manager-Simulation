document.addEventListener('DOMContentLoaded', function () {
  const rendered = new Set();

  document.querySelectorAll('.collapse').forEach(function (collapseEl) {
    collapseEl.addEventListener('shown.bs.collapse', function () {
      const runId = collapseEl.id.replace('run-', '');
      if (rendered.has(runId)) return;

      const raw = (window.runStats && window.runStats[runId]) || [];
      if (!raw.length) return;

      const canvas = document.getElementById('chart-' + runId);
      if (!canvas) return;

      const labels        = raw.map(d => 'Day ' + d.day);
      const progressData  = raw.map(d => d.progress_gained  ?? 0);
      const scoreData     = raw.map(d => d.score_gained     ?? 0);
      const failData      = raw.map(d => d.tasks_failed     ?? 0);

      new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Progress Gained',
              data: progressData,
              backgroundColor: 'rgba(13, 110, 253, 0.25)',
              borderColor: 'rgba(13, 110, 253, 0.8)',
              borderWidth: 1,
              order: 2,
            },
            {
              label: 'Score Gained',
              data: scoreData,
              type: 'line',
              borderColor: 'rgba(25, 135, 84, 0.9)',
              borderWidth: 2,
              pointRadius: 3,
              tension: 0.3,
              fill: false,
              order: 1,
            },
            {
              label: 'Tasks Failed',
              data: failData,
              backgroundColor: 'rgba(220, 53, 69, 0.6)',
              borderColor: 'rgba(220, 53, 69, 0.9)',
              borderWidth: 1,
              order: 3,
            },
          ],
        },
        options: {
          responsive: true,
          interaction: { mode: 'index', intersect: false },
          plugins: { legend: { position: 'bottom' } },
          scales: {
            y: { beginAtZero: true },
            x: { ticks: { maxRotation: 45 } },
          },
        },
      });

      rendered.add(runId);
    });
  });
});