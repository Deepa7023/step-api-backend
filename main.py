<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>CAD-driven HPDC Estimator</title>

  <style>
    /* ---------- Global ---------- */
    body {
      margin: 0;
      font-family: "Segoe UI", Roboto, Arial, sans-serif;
      background: #f6f8f7;
      color: #1f2937;
    }

    /* ---------- Layout ---------- */
    .app-layout {
      display: grid;
      grid-template-columns: 360px 1fr; /* ✅ Left panel expanded */
      height: 100vh;
    }

    /* ---------- Left Panel ---------- */
    .left-panel {
      background: #ffffff;
      border-right: 1px solid #e5e7eb;
      padding: 20px;
      font-size: 0.95rem; /* ✅ Slight font increase */
    }

    .heading-primary {
      font-size: 1.15rem;
      font-weight: 700; /* ✅ Bold heading */
      margin-bottom: 6px;
    }

    .heading-sub {
      font-size: 0.85rem;
      color: #6b7280;
      margin-bottom: 20px;
    }

    .left-section {
      margin-bottom: 20px;
    }

    .label {
      font-size: 0.8rem;
      color: #6b7280;
      margin-bottom: 4px;
    }

    .value {
      font-weight: 600;
      padding: 8px 10px;
      border: 1px dashed #10b981;
      border-radius: 6px;
      background: #ecfdf5;
    }

    .button {
      margin-top: 20px;
      width: 100%;
      padding: 10px;
      background: linear-gradient(90deg, #10b981, #f59e0b);
      border: none;
      border-radius: 6px;
      font-size: 0.9rem;
      font-weight: 600;
      color: #ffffff;
      cursor: pointer;
    }

    /* ---------- Main Content ---------- */
    .main-content {
      padding: 24px;
      overflow-y: auto;
    }

    .card {
      background: #ffffff;
      border-radius: 10px;
      padding: 20px;
      margin-bottom: 16px;
      border: 1px solid #e5e7eb;
    }

    /* ---------- Section Headings ---------- */
    .section-heading {
      font-size: 0.95rem;
      font-weight: 600;
      margin-bottom: 12px;
      color: #065f46;
    }

    /* ---------- Geometry Grid ---------- */
    .geometry-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }

    .metric {
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      padding: 10px 12px;
      background: #ffffff;
    }

    .metric-label {
      font-size: 0.75rem;
      color: #6b7280;
    }

    .metric-value {
      font-size: 0.9rem;
      font-weight: 600;
      margin-top: 4px;
    }

    /* ---------- Cost ---------- */
    .cost-value {
      font-size: 1.6rem;
      font-weight: 700;
      color: #047857;
    }

    .cost-range {
      font-size: 0.8rem;
      color: #f97316;
    }

  </style>
</head>

<body>

  <div class="app-layout">

    <!-- ================= Left Panel ================= -->
    <aside class="left-panel">
      <div class="heading-primary">CAD‑driven HPDC estimator</div>
      <div class="heading-sub">Engineer cost intelligence console</div>

      <div class="left-section">
        <div class="label">CAD file</div>
        <div class="value">XU‑EM0902‑300_A.stp</div>
      </div>

      <div class="left-section">
        <div class="label">Manufacturing location</div>
        <div class="value">India (Pune)</div>
      </div>

      <div class="left-section">
        <div class="label">Alloy</div>
        <div class="value">Aluminum A356</div>
      </div>

      <div class="left-section">
        <div class="label">Pieces per year</div>
        <div class="value">12,000</div>
      </div>

      <button class="button">Run per‑part estimation</button>
    </aside>

    <!-- ================= Main Content ================= -->
    <main class="main-content">

      <!-- Cost -->
      <div class="card">
        <div class="section-heading">Per‑part HPDC cost (Estimated)</div>
        <div class="cost-value">₹772.48</div>
        <div class="cost-range">Expected range: ₹718.41 – ₹826.55</div>
      </div>

      <!-- Geometry -->
      <div class="card">
        <div class="section-heading">▸ Geometry extracted from CAD</div>

        <div class="geometry-grid">
          <div class="metric">
            <div class="metric-label">Bounding box X (mm)</div>
            <div class="metric-value">95.17</div>
          </div>

          <div class="metric">
            <div class="metric-label">Bounding box Y (mm)</div>
            <div class="metric-value">62.18</div>
          </div>

          <div class="metric">
            <div class="metric-label">Bounding box Z (mm)</div>
            <div class="metric-value">52.18</div>
          </div>

          <div class="metric">
            <div class="metric-label">Volume (cm³)</div>
            <div class="metric-value">183.47</div>
          </div>

          <div class="metric">
            <div class="metric-label">Surface area (cm²)</div>
            <div class="metric-value">513.92</div>
          </div>

          <div class="metric">
            <div class="metric-label">Casting weight (kg)</div>
            <div class="metric-value">0.49</div>
          </div>

          <div class="metric">
            <div class="metric-label">Estimated projected area (cm²)</div>
            <div class="metric-value">491.7</div>
          </div>

          <div class="metric">
            <div class="metric-label">Estimated HPDC tonnage</div>
            <div class="metric-value">780 T</div>
          </div>
        </div>
      </div>

    </main>
  </div>

</body>
</html>
