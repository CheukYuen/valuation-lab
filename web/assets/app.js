(() => {
  const KEY = "valuation-lab-progress-v1";
  const NOTE_PREFIX = "valuation-lab-note:";
  const STUDY_PREFIX = "valuation-lab-study:";

  function readProgress() {
    try { return JSON.parse(localStorage.getItem(KEY) || "{}"); }
    catch { return {}; }
  }

  function writeProgress(value) {
    localStorage.setItem(KEY, JSON.stringify(value));
    renderProgress();
  }

  function completedCount() {
    const p = readProgress();
    return Array.from({ length: 7 }, (_, i) => p[`day-${i + 1}`]).filter(Boolean).length;
  }

  function renderProgress() {
    const done = completedCount();
    document.querySelectorAll("[data-progress-bar]").forEach(el => { el.style.width = `${done / 7 * 100}%`; });
    document.querySelectorAll("[data-progress-text]").forEach(el => { el.textContent = `${done}/7` ; });
    document.querySelectorAll("[data-progress-percent]").forEach(el => { el.textContent = `${Math.round(done / 7 * 100)}%`; });
    document.querySelectorAll("[data-lesson-card]").forEach(card => {
      const isDone = Boolean(readProgress()[card.dataset.lessonCard]);
      card.classList.toggle("done", isDone);
      const status = card.querySelector(".status");
      if (status) status.textContent = isDone ? "已完成" : "待学习";
    });
    const lesson = document.body.dataset.lesson;
    const complete = document.querySelector("[data-complete-lesson]");
    if (lesson && complete) complete.textContent = readProgress()[lesson] ? "已完成本课 ✓" : "标记本课完成";
  }

  function setupQuizzes() {
    document.querySelectorAll(".quiz-card").forEach(card => {
      const correct = card.dataset.answer;
      const explanation = card.dataset.explanation || "";
      card.querySelectorAll("[data-choice]").forEach(button => {
        button.addEventListener("click", () => {
          card.querySelectorAll("[data-choice]").forEach(b => b.classList.remove("correct", "incorrect"));
          const ok = button.dataset.choice === correct;
          button.classList.add(ok ? "correct" : "incorrect");
          const feedback = card.querySelector(".feedback");
          feedback.className = `feedback ${ok ? "correct" : "incorrect"}`;
          feedback.textContent = `${ok ? "正确。" : "再想一步。"}${explanation}`;
        });
      });
    });
  }

  function setupNotes() {
    document.querySelectorAll("[data-note]").forEach(area => {
      const key = NOTE_PREFIX + (area.dataset.note || location.pathname);
      area.value = localStorage.getItem(key) || "";
      area.addEventListener("input", () => localStorage.setItem(key, area.value));
    });
  }

  function setupCompletion() {
    const button = document.querySelector("[data-complete-lesson]");
    const lesson = document.body.dataset.lesson;
    if (!button || !lesson) return;
    button.addEventListener("click", () => {
      const p = readProgress();
      p[lesson] = !p[lesson];
      writeProgress(p);
    });
  }

  function setupStudyChecks() {
    document.querySelectorAll("[data-study-check]").forEach(box => {
      const key = STUDY_PREFIX + box.dataset.studyCheck;
      box.checked = localStorage.getItem(key) === "1";
      box.addEventListener("change", () => localStorage.setItem(key, box.checked ? "1" : "0"));
    });
  }

  function setupReset() {
    document.querySelectorAll("[data-reset-progress]").forEach(button => {
      button.addEventListener("click", () => {
        if (!confirm("清除7课完成记录和本页学习勾选？笔记不会删除。")) return;
        localStorage.removeItem(KEY);
        Object.keys(localStorage).filter(k => k.startsWith(STUDY_PREFIX)).forEach(k => localStorage.removeItem(k));
        location.reload();
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    setupQuizzes();
    setupNotes();
    setupCompletion();
    setupStudyChecks();
    setupReset();
    renderProgress();
  });
})();
