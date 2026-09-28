/**
 * YourWebMind — Evaluator-First Frontend Logic
 * Pure vanilla JavaScript with zero external dependencies.
 * Consumes deterministic YourWebMind backend APIs.
 */

(function () {
  'use strict';

  // API Base
  const API_BASE = '/api/v1';

  // DOM Elements: Navigation & Loop
  const btnRunAnalysis = document.getElementById('btn-run-analysis');
  const btnReset = document.getElementById('btn-reset');
  const loopCurrentStatus = document.getElementById('loop-current-status');
  const loopSteps = document.getElementById('loop-steps');

  // Signal Elements
  const signalPage = document.getElementById('signal-page');
  const signalUrl = document.getElementById('signal-url');
  const signalKeyword = document.getElementById('signal-keyword');
  const signalCurrentCtr = document.getElementById('signal-current-ctr');
  const signalPrevCtr = document.getElementById('signal-prev-ctr');
  const signalRank = document.getElementById('signal-rank');
  const signalRankSub = document.getElementById('signal-rank-sub');
  const signalImpressions = document.getElementById('signal-impressions');
  const signalClicks = document.getElementById('signal-clicks');
  const signalSummary = document.getElementById('signal-summary');

  // Recommendation Elements
  const badgeApprovalStatus = document.getElementById('badge-approval-status');
  const recActionText = document.getElementById('rec-action-text');
  const recRationale = document.getElementById('rec-rationale');
  const recImpact = document.getElementById('rec-impact');
  const recConfidence = document.getElementById('rec-confidence');

  // Approval Elements
  const inputOperatorNote = document.getElementById('input-operator-note');
  const btnApprove = document.getElementById('btn-approve');
  const btnReject = document.getElementById('btn-reject');
  const approvalPendingControls = document.getElementById('approval-pending-controls');
  const approvalApprovedBanner = document.getElementById('approval-approved-banner');
  const approvalRejectedBanner = document.getElementById('approval-rejected-banner');
  const approvedNoteDisplay = document.getElementById('approved-note-display');
  const rejectedNoteDisplay = document.getElementById('rejected-note-display');
  const approvedTimestamp = document.getElementById('approved-timestamp');
  const btnRunExperiment = document.getElementById('btn-run-experiment');
  const btnReconsider = document.getElementById('btn-reconsider');

  // Experiment & Retained Elements
  const sectionExperiment = document.getElementById('section-experiment');
  const expId = document.getElementById('exp-id');
  const expMetric = document.getElementById('exp-metric');
  const expBaseline = document.getElementById('exp-baseline');
  const expMeasured = document.getElementById('exp-measured');
  const expAbsChange = document.getElementById('exp-abs-change');
  const expRelChange = document.getElementById('exp-rel-change');
  const expFactualText = document.getElementById('exp-factual-text');
  const badgeOutcomeClass = document.getElementById('badge-outcome-class');

  const sectionRetainedLesson = document.getElementById('section-retained-lesson');
  const lessonText = document.getElementById('lesson-text');
  const retainedDocId = document.getElementById('retained-doc-id');
  const futureVerificationText = document.getElementById('future-verification-text');

  // Historical & Reasoning Elements
  const memTotalCount = document.getElementById('mem-total-count');
  const memPosCount = document.getElementById('mem-pos-count');
  const memNegCount = document.getElementById('mem-neg-count');
  const memNeuCount = document.getElementById('mem-neu-count');
  const memIncCount = document.getElementById('mem-inc-count');
  const evidenceCompactList = document.getElementById('evidence-compact-list');

  const reasoningSynthesis = document.getElementById('reasoning-synthesis');
  const reasoningSupporting = document.getElementById('reasoning-supporting');
  const reasoningConflicting = document.getElementById('reasoning-conflicting');
  const reasoningCaveat = document.getElementById('reasoning-caveat');
  const reflectNoteText = document.getElementById('reflect-note-text');

  // Memory Browser Elements
  const formMemorySearch = document.getElementById('form-memory-search');
  const inputMemorySearch = document.getElementById('input-memory-search');
  const memoryCardsList = document.getElementById('memory-cards-list');
  const filterPills = document.querySelectorAll('.filter-pills .pill');
  const countAll = document.getElementById('count-all');
  const countPos = document.getElementById('count-pos');
  const countNeg = document.getElementById('count-neg');
  const countNeu = document.getElementById('count-neu');
  const countInc = document.getElementById('count-inc');

  // State
  let currentOutcomeFilter = 'all';
  let memoryDataCache = [];

  // Helper: Format badge outcome class
  function getOutcomeBadgeClass(outcome) {
    switch ((outcome || '').toLowerCase()) {
      case 'positive': return 'badge-positive';
      case 'negative': return 'badge-negative';
      case 'neutral': return 'badge-neutral';
      case 'inconclusive': return 'badge-inconclusive';
      default: return 'badge-demo';
    }
  }

  // Update The Learning Loop Step Indicators (10 stages)
  function updateLearningLoop(stage) {
    const steps = loopSteps.querySelectorAll('.step');
    const stageMap = {
      'observe': 1,
      'current_data': 1,
      'recall': 2,
      'compare': 3,
      'historical_evidence': 3,
      'reason': 4,
      'reflect': 4,
      'recommend': 5,
      'approve': 6,
      'approval': 6,
      'approved': 6,
      'rejected': 6,
      'experiment': 7,
      'measure': 8,
      'outcome': 8,
      'retain': 9,
      'learn': 10,
      'future_learning': 10,
      'completed': 10
    };

    const activeIndex = stageMap[stage] || 6;

    steps.forEach((step, idx) => {
      const stepNum = idx + 1;
      step.classList.remove('step-completed', 'step-active');
      if (stepNum < activeIndex) {
        step.classList.add('step-completed');
      } else if (stepNum === activeIndex) {
        if (stage === 'completed') {
          step.classList.add('step-completed');
        } else {
          step.classList.add('step-active');
        }
      }
    });

    if (stage === 'completed') {
      loopCurrentStatus.textContent = 'Stage 10/10: Complete — Lesson Retained & Available';
    } else if (stage === 'approved') {
      loopCurrentStatus.textContent = 'Stage 06/10: Recommendation Approved — Ready to Run Experiment';
    } else if (stage === 'rejected') {
      loopCurrentStatus.textContent = 'Stage 06/10: Recommendation Rejected — Execution Halted';
    } else {
      loopCurrentStatus.textContent = 'Stage 06/10: Human Approval Gateway (Pending)';
    }
  }

  // 1. Load Initial Demo Analysis
  async function loadDemoAnalysis() {
    try {
      const res = await fetch(`${API_BASE}/agent/demo-analysis`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      renderAnalysis(data);
    } catch (err) {
      console.error('Failed to load demo analysis:', err);
      signalSummary.textContent = 'Historical memory temporarily unavailable. Running in local fallback mode.';
    }
  }

  // Render Analysis Data into View
  function renderAnalysis(data) {
    const sig = data.signal;
    const mem = data.historical_memory;
    const lrn = data.learning;
    const rec = data.recommendation;

    // Signal Section
    signalPage.textContent = sig.page_title;
    signalUrl.textContent = sig.page_url;
    signalUrl.href = sig.page_url;
    signalKeyword.textContent = sig.keyword;
    signalCurrentCtr.textContent = `${sig.current_ctr.toFixed(2)}%`;
    signalPrevCtr.textContent = `${sig.previous_ctr.toFixed(2)}% previous`;
    signalRank.textContent = sig.rank.toFixed(1);
    signalRankSub.textContent = `Maintained top-3 rank (prev: ${sig.previous_rank.toFixed(1)})`;
    signalImpressions.textContent = sig.impressions.toLocaleString();
    signalClicks.textContent = `${sig.clicks.toLocaleString()} clicks (observed)`;
    signalSummary.textContent = sig.signal_description;

    // Historical Memory Section Counts
    memTotalCount.textContent = mem.relevant_count;
    memPosCount.textContent = mem.positive_count;
    memNegCount.textContent = mem.negative_count;
    memNeuCount.textContent = mem.neutral_count;
    memIncCount.textContent = mem.inconclusive_count;

    // Render Compact Evidence Cards List
    evidenceCompactList.innerHTML = '';
    mem.evidence_list.forEach(item => {
      const li = document.createElement('li');
      const outcome = (item.outcome || '').toLowerCase();
      const badgeCls = getOutcomeBadgeClass(item.outcome);

      let roleLabel = 'Contextual Precedent';
      let roleClass = 'role-contextual';
      if (outcome === 'positive') {
        roleLabel = 'Supporting precedent';
        roleClass = 'role-supporting';
      } else if (outcome === 'negative') {
        roleLabel = 'Conflicting precedent';
        roleClass = 'role-conflicting';
      } else if (outcome === 'neutral') {
        roleLabel = 'Neutral precedent';
        roleClass = 'role-neutral';
      } else if (outcome === 'inconclusive') {
        roleLabel = 'Inconclusive precedent';
        roleClass = 'role-inconclusive';
      }

      li.className = `evidence-card-item ${roleClass}`;
      li.innerHTML = `
        <div class="evidence-card-top">
          <div class="evidence-identity">
            <span class="evidence-id font-mono">${item.experiment_id.toUpperCase()}</span>
            <span class="evidence-type">${item.technique || 'Title Tag Strategy'}</span>
          </div>
          <div class="evidence-outcome-wrap">
            <span class="badge ${badgeCls}">${item.outcome.toUpperCase()}</span>
            <span class="evidence-delta font-mono">${item.delta}</span>
          </div>
        </div>
        <div class="evidence-summary-text">${item.summary}</div>
        <div class="evidence-role-tag font-mono">${roleLabel}</div>
      `;
      evidenceCompactList.appendChild(li);
    });

    // Why This Recommendation / Evidence Synthesis Section
    reasoningSynthesis.textContent = `“${lrn.synthesis}”`;
    reasoningSupporting.textContent = lrn.relevant_evidence;
    reasoningConflicting.textContent = lrn.conflicting_evidence;
    reasoningCaveat.textContent = lrn.caveat;

    if (lrn.reflect_status_note) {
      reflectNoteText.textContent = lrn.reflect_status_note;
    } else if (data.demo_mode) {
      reflectNoteText.textContent = 'Reasoning synthesized via deterministic contextual precedent evaluation.';
    } else {
      reflectNoteText.textContent = 'Reasoning synthesized with Hindsight Reflect.';
    }

    // Dynamic Memory Browser Header based on demo/live mode
    const headingBrowser = document.getElementById('heading-browser');
    const browserIntro = document.querySelector('.browser-intro');
    if (data.demo_mode) {
      if (headingBrowser) headingBrowser.textContent = 'Search YourWebMind SEO Memory';
      if (browserIntro) browserIntro.textContent = 'Search the deterministic demo experiment records to explore positive, negative, neutral, and inconclusive precedents.';
    } else {
      if (headingBrowser) headingBrowser.textContent = 'Search Hindsight SEO Memory';
      if (browserIntro) browserIntro.textContent = 'Query persistent experiment records retained in Hindsight to explore precedents across positive, negative, and inconclusive tests.';
    }

    // Recommendation Section
    recActionText.textContent = rec.action;
    recRationale.textContent = rec.rationale;
    recImpact.textContent = rec.expected_impact;
    recConfidence.innerHTML = `<strong>${Math.round(rec.confidence * 100)}%</strong> <span class="text-muted">(${rec.confidence.toFixed(2)} bounded: 0.10 to 0.85)</span>`;

    // Approval Gateway Initial State
    setApprovalState(data.approval.status, data.approval.operator_note);

    // If experiment already executed in this session
    if (data.experiment && data.outcome) {
      renderExperimentResult(data.experiment, data.outcome, data.retained_lesson, data.retain_info, data.future_learning);
      updateLearningLoop('completed');
    } else if (data.approval.status === 'APPROVED') {
      updateLearningLoop('approved');
    } else if (data.approval.status === 'REJECTED') {
      updateLearningLoop('rejected');
    } else {
      updateLearningLoop('approval');
    }
  }

  // Set Approval State UI
  function setApprovalState(status, note) {
    badgeApprovalStatus.textContent = status;
    badgeApprovalStatus.className = 'badge';

    if (status === 'APPROVED') {
      badgeApprovalStatus.classList.add('badge-positive');
      approvalPendingControls.classList.add('hidden');
      approvalApprovedBanner.classList.remove('hidden');
      approvalRejectedBanner.classList.add('hidden');
      approvedNoteDisplay.textContent = note ? `Operator note: ${note}` : 'Operator approval granted.';
      approvedTimestamp.textContent = `Recorded: ${new Date().toLocaleTimeString()}`;
    } else if (status === 'REJECTED') {
      badgeApprovalStatus.classList.add('badge-negative');
      approvalPendingControls.classList.add('hidden');
      approvalApprovedBanner.classList.add('hidden');
      approvalRejectedBanner.classList.remove('hidden');
      rejectedNoteDisplay.textContent = note ? `Reason: ${note}` : 'Recommendation rejected by operator. Execution halted.';
    } else {
      // Pending
      badgeApprovalStatus.classList.add('badge-approval');
      approvalPendingControls.classList.remove('hidden');
      approvalApprovedBanner.classList.add('hidden');
      approvalRejectedBanner.classList.add('hidden');
    }
  }

  // 2. Handle Operator Approval
  async function handleApproval(approved) {
    const note = inputOperatorNote.value.trim();
    try {
      const res = await fetch(`${API_BASE}/agent/approval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved, operator_note: note })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setApprovalState(data.approval_status, data.operator_note);
      updateLearningLoop(approved ? 'approved' : 'rejected');
    } catch (err) {
      console.error('Failed to submit approval:', err);
      alert('Could not record approval decision. Please retry.');
    }
  }

  // 3. Handle Controlled Experiment Execution
  async function handleRunExperiment() {
    btnRunExperiment.disabled = true;
    btnRunExperiment.textContent = 'Executing Controlled Trial...';

    try {
      const res = await fetch(`${API_BASE}/agent/execute-experiment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ measured_value: 2.70 })
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      renderExperimentResult(data.experiment, data.outcome, data.lesson, data.retain_info, data.future_learning);
      updateLearningLoop('completed');

      // Refresh Memory Browser to show new retained memory at top
      loadMemoryBrowser(inputMemorySearch.value.trim());

      // Smoothly scroll to the experiment result
      sectionExperiment.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      console.error('Failed to execute experiment:', err);
      alert(`Experiment execution failed: ${err.message}`);
    } finally {
      btnRunExperiment.disabled = false;
      btnRunExperiment.textContent = 'Run Controlled Experiment';
    }
  }

  // Render Experiment & Retained Result
  function renderExperimentResult(exp, out, lesson, retainInfo, futureLearning) {
    sectionExperiment.classList.remove('hidden');
    sectionRetainedLesson.classList.remove('hidden');

    // Experiment Stats
    expId.textContent = exp.experiment_id;
    expMetric.textContent = exp.metric;
    expBaseline.textContent = `${exp.baseline.toFixed(2)}%`;
    expMeasured.textContent = `${exp.measured.toFixed(2)}%`;
    expAbsChange.textContent = `${out.absolute_change} percentage points`;
    expRelChange.textContent = `${out.relative_change} relative change`;
    expFactualText.textContent = `“${out.factual_statement}”`;
    badgeOutcomeClass.textContent = `OUTCOME: ${out.classification}`;
    badgeOutcomeClass.className = `badge ${getOutcomeBadgeClass(out.classification)}`;

    // Retained Lesson
    lessonText.textContent = lesson;
    retainedDocId.textContent = retainInfo.memory_doc_id;
    if (futureLearning && futureLearning.verification_note) {
      futureVerificationText.textContent = `Verification: ${futureLearning.verification_note}`;
    }
  }

  // 4. Reset Demo State
  async function handleResetDemo() {
    if (!confirm('Reset the YourWebMind demonstration back to the initial pre-approval state?')) return;
    try {
      await fetch(`${API_BASE}/agent/reset`, { method: 'POST' });
      sectionExperiment.classList.add('hidden');
      sectionRetainedLesson.classList.add('hidden');
      loadDemoAnalysis();
      loadMemoryBrowser('waterproof hiking boots');
    } catch (err) {
      console.error('Failed to reset demo:', err);
    }
  }

  // 5. Memory Browser Logic
  async function loadMemoryBrowser(query = '') {
    try {
      const url = new URL(`${window.location.origin}${API_BASE}/memory/browse`);
      if (query) url.searchParams.set('q', query);
      if (currentOutcomeFilter && currentOutcomeFilter !== 'all') {
        url.searchParams.set('outcome', currentOutcomeFilter);
      }

      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      memoryDataCache = data.memories || [];
      renderMemoryCards(memoryDataCache);
      updateMemoryCounts(memoryDataCache);
    } catch (err) {
      console.error('Failed to load memory browser:', err);
      memoryCardsList.innerHTML = '<div class="text-muted" style="padding: 12px;">Memory records temporarily unavailable.</div>';
    }
  }

  // Render Memory Cards in Browser
  function renderMemoryCards(items) {
    memoryCardsList.innerHTML = '';
    if (!items || items.length === 0) {
      memoryCardsList.innerHTML = '<div class="text-muted font-mono" style="padding: 24px; text-align: center;">No matching experiments found in memory bank.</div>';
      return;
    }

    items.forEach(item => {
      const card = document.createElement('article');
      card.className = 'mem-card';
      const badgeCls = getOutcomeBadgeClass(item.outcome);
      const isRetainedDemo = item.experiment_id === 'EXP-021-DEMO';

      card.innerHTML = `
        <div class="mem-card-top">
          <div class="mem-card-title-group">
            <span class="mem-card-id font-mono">${item.experiment_id}</span>
            ${isRetainedDemo ? '<span class="badge badge-demo badge-retained-new">NEWLY RETAINED PRECEDENT</span>' : ''}
          </div>
          <div class="mem-card-status-group">
            <span class="badge ${badgeCls}">${(item.outcome || 'UNKNOWN').toUpperCase()}</span>
            <span class="mem-card-delta font-mono">${item.delta}</span>
          </div>
        </div>
        <div class="mem-card-tech">${item.technique}</div>
        <div class="mem-card-context">${item.context || ''}</div>
        ${item.caveat ? `<div class="mem-card-caveat font-mono">Caveat: ${item.caveat}</div>` : ''}
      `;
      memoryCardsList.appendChild(card);
    });
  }

  // Update Memory Counts in Filter Pills
  function updateMemoryCounts(items) {
    let pos = 0, neg = 0, neu = 0, inc = 0;
    items.forEach(it => {
      const o = (it.outcome || '').toLowerCase();
      if (o === 'positive') pos++;
      else if (o === 'negative') neg++;
      else if (o === 'neutral') neu++;
      else if (o === 'inconclusive') inc++;
    });

    countAll.textContent = items.length;
    countPos.textContent = pos;
    countNeg.textContent = neg;
    countNeu.textContent = neu;
    countInc.textContent = inc;
  }

  // Attach Event Listeners
  function attachEvents() {
    btnRunAnalysis.addEventListener('click', loadDemoAnalysis);
    btnReset.addEventListener('click', handleResetDemo);

    btnApprove.addEventListener('click', () => handleApproval(true));
    btnReject.addEventListener('click', () => handleApproval(false));
    btnRunExperiment.addEventListener('click', handleRunExperiment);

    btnReconsider.addEventListener('click', () => {
      setApprovalState('PENDING APPROVAL', null);
      updateLearningLoop('approval');
    });

    // Memory Search Form
    formMemorySearch.addEventListener('submit', (e) => {
      e.preventDefault();
      loadMemoryBrowser(inputMemorySearch.value.trim());
    });

    // Memory Filter Pills
    filterPills.forEach(pill => {
      pill.addEventListener('click', () => {
        filterPills.forEach(p => p.classList.remove('pill-active'));
        pill.classList.add('pill-active');
        currentOutcomeFilter = pill.getAttribute('data-outcome');
        loadMemoryBrowser(inputMemorySearch.value.trim());
      });
    });
  }

  // Initialize
  function init() {
    attachEvents();
    loadDemoAnalysis();
    loadMemoryBrowser('waterproof hiking boots');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
