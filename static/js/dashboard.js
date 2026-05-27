 // =========================
  // DATE
  // =========================
  const now = new Date();

  document.getElementById('live-date').textContent =
    now.toLocaleDateString('en-PH', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });

  document.getElementById('today-label').textContent =
    now.toLocaleDateString('en-PH', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });

  // =========================
  // DATA FROM FLASK
  // =========================
  const barLabels = {{ bar_labels | tojson | safe }};
  const barData = {{ bar_data | tojson | safe }};

  const donutData = [
    {{ counts.approved or 0 }},
    {{ counts.pending or 0 }},
    {{ counts.rescheduled or 0 }},
    {{ counts.cancelled or 0 }},
    {{ counts.completed or 0 }}
  ];



  // =========================
  // BAR CHART
  // =========================
  const barChartCanvas = document.getElementById('barChart');

  new Chart(barChartCanvas, {
    type: 'bar',

    data: {
      labels: barLabels,

      datasets: [
        {
          label: 'Appointments',
          data: barData,
          backgroundColor: '#2A7A62',
          borderRadius: 8,
          borderSkipped: false,
          maxBarThickness: 42
        }
      ]
    },

    options: {
      responsive: true,
      maintainAspectRatio: false,

      plugins: {
        legend: {
          display: false
        },

        tooltip: {
          backgroundColor: '#1F2937',
          padding: 10,

          callbacks: {
            label: function(context) {
              return `${context.raw} appointment(s)`;
            }
          }
        }
      },

      scales: {
        x: {
          grid: {
            display: false
          },

          ticks: {
            color: '#5A7A72',
            autoSkip: false,

            font: {
              size: 10
            }
          }
        },

        y: {
          beginAtZero: true,

          grid: {
            color: 'rgba(0,0,0,0.04)'
          },

          ticks: {
            stepSize: 1,
            precision: 0,
            color: '#5A7A72',

            font: {
              size: 10
            }
          }
        }
      }
    }
  });



  // =========================
  // DONUT CHART
  // =========================
  const donutChartCanvas = document.getElementById('donutChart');

  new Chart(donutChartCanvas, {
    type: 'doughnut',

    data: {
      labels: [
        'Approved',
        'Pending',
        'Rescheduled',
        'Cancelled',
        'Completed'
      ],

      datasets: [
        {
          data: donutData,

          backgroundColor: [
            '#10B981',
            '#F59E0B',
            '#3B82F6',
            '#EF4444',
            '#6B7280'
          ],

          borderWidth: 0,
          hoverOffset: 6
        }
      ]
    },

    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',

      plugins: {
        legend: {
          display: false
        },

        tooltip: {
          backgroundColor: '#1F2937',
          padding: 10,

          callbacks: {
            label: function(context) {
              return `${context.label}: ${context.raw}`;
            }
          }
        }
      }
    }
  });


  