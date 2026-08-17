(() => {
  const KEY = "valuation-lab-progress-v1";
  const NOTE_PREFIX = "valuation-lab-note:";
  const STUDY_PREFIX = "valuation-lab-study:";
  const QUIZ_PREFIX = "valuation-lab-quiz:";
  const READ_PREFIX = "valuation-lab-read:";

  const LESSONS = [
    { id: "day-1", title: "模型到底在说什么" },
    { id: "day-2", title: "看懂最小价值桥" },
    { id: "day-3", title: "五分钟初筛" },
    { id: "day-4", title: "谁在控制结果" },
    { id: "day-5", title: "反向 DCF" },
    { id: "day-6", title: "方法适不适合" },
    { id: "day-7", title: "长飞毕业审计" },
  ];

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
    return LESSONS.filter(lesson => p[lesson.id]).length;
  }

  function firstIncompleteLesson() {
    const p = readProgress();
    return LESSONS.find(lesson => !p[lesson.id]) || null;
  }

  function readQuizRecord(key) {
    try { return JSON.parse(localStorage.getItem(key) || "null"); }
    catch { return null; }
  }

  function renderProgress() {
    const done = completedCount();
    document.querySelectorAll("[data-progress-bar]").forEach(el => { el.style.width = `${done / 7 * 100}%`; });
    document.querySelectorAll("[data-progress-text]").forEach(el => { el.textContent = `${done}/7`; });
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
    renderResumeLink();
    renderDayDots();
    renderCourseSwitcher();
    renderQuizScore();
    renderHomeStats();
  }

  function renderResumeLink() {
    const links = document.querySelectorAll("[data-resume-link]");
    if (!links.length) return;
    const next = firstIncompleteLesson();
    links.forEach(link => {
      if (!next) {
        link.href = "../course/POSTTEST.md";
        link.textContent = "全部完成 · 开始毕业测验";
      } else if (next.id === "day-1") {
        link.href = "day-1.html";
        link.textContent = "从第1课开始";
      } else {
        link.href = `${next.id}.html`;
        link.textContent = `继续第${next.id.replace("day-", "")}课`;
      }
    });
  }

  function renderDayDots() {
    const containers = document.querySelectorAll("[data-day-dots]");
    if (!containers.length) return;
    const p = readProgress();
    const current = document.body.dataset.lesson;
    containers.forEach(container => {
      container.innerHTML = "";
      LESSONS.forEach(lesson => {
        const dot = document.createElement("span");
        dot.className = "day-dot";
        if (p[lesson.id]) dot.classList.add("done");
        if (lesson.id === current) dot.classList.add("current");
        dot.title = `${lesson.title}${p[lesson.id] ? " · 已完成" : ""}`;
        container.appendChild(dot);
      });
    });
  }

  function renderCourseSwitcher() {
    const lists = document.querySelectorAll("[data-course-switcher-list]");
    if (!lists.length) return;
    const p = readProgress();
    const current = document.body.dataset.lesson;
    lists.forEach(list => {
      list.innerHTML = "";
      LESSONS.forEach(lesson => {
        const link = document.createElement("a");
        link.href = `${lesson.id}.html`;
        link.className = "course-switcher-item";
        if (lesson.id === current) link.classList.add("current");
        const isDone = Boolean(p[lesson.id]);
        link.innerHTML = `<span class="course-switcher-mark${isDone ? " done" : ""}" aria-hidden="true">${isDone ? "✓" : lesson.id.replace("day-", "")}</span><span>${lesson.title}</span>`;
        list.appendChild(link);
      });
    });
    document.querySelectorAll("[data-course-switcher-current]").forEach(el => {
      const found = LESSONS.find(lesson => lesson.id === current);
      if (found) el.textContent = `7天课程 · 第${current.replace("day-", "")}天`;
    });
  }

  function quizKey(card, index) {
    const lesson = document.body.dataset.lesson || location.pathname;
    const id = card.dataset.quizId || `q${index}`;
    return `${QUIZ_PREFIX}${lesson}:${id}`;
  }

  function applyQuizChoice(card, choiceValue) {
    const correct = card.dataset.answer;
    const explanation = card.dataset.explanation || "";
    card.querySelectorAll("[data-choice]").forEach(b => b.classList.remove("correct", "incorrect"));
    const button = Array.from(card.querySelectorAll("[data-choice]")).find(b => b.dataset.choice === choiceValue);
    if (!button) return;
    const ok = choiceValue === correct;
    button.classList.add(ok ? "correct" : "incorrect");
    const feedback = card.querySelector(".feedback");
    if (feedback) {
      feedback.className = `feedback ${ok ? "correct" : "incorrect"}`;
      feedback.textContent = `${ok ? "正确。" : "再想一步。"}${explanation}`;
    }
  }

  function setupQuizzes() {
    document.querySelectorAll(".quiz-card").forEach((card, index) => {
      const key = quizKey(card, index);
      const saved = readQuizRecord(key);
      if (saved) applyQuizChoice(card, saved.choice);
      card.querySelectorAll("[data-choice]").forEach(button => {
        button.addEventListener("click", () => {
          applyQuizChoice(card, button.dataset.choice);
          const ok = button.dataset.choice === card.dataset.answer;
          localStorage.setItem(key, JSON.stringify({ choice: button.dataset.choice, ok }));
          renderQuizScore();
          renderHomeStats();
        });
      });
    });
  }

  function renderQuizScore() {
    const cards = document.querySelectorAll(".quiz-card");
    const targets = document.querySelectorAll("[data-quiz-score]");
    if (!cards.length || !targets.length) return;
    let correctCount = 0;
    let answeredCount = 0;
    cards.forEach((card, index) => {
      const rec = readQuizRecord(quizKey(card, index));
      if (rec) {
        answeredCount += 1;
        if (rec.ok) correctCount += 1;
      }
    });
    targets.forEach(el => {
      el.textContent = answeredCount === 0
        ? `${cards.length} 题未开始`
        : `${correctCount} / ${cards.length} 题正确`;
    });
  }

  function renderHomeStats() {
    const containers = document.querySelectorAll("[data-home-stats]");
    if (!containers.length) return;
    let totalAnswered = 0;
    let totalCorrect = 0;
    Object.keys(localStorage).filter(k => k.startsWith(QUIZ_PREFIX)).forEach(k => {
      const rec = readQuizRecord(k);
      if (rec) {
        totalAnswered += 1;
        if (rec.ok) totalCorrect += 1;
      }
    });
    const noteCount = Object.keys(localStorage).filter(k => {
      if (!k.startsWith(NOTE_PREFIX)) return false;
      return (localStorage.getItem(k) || "").trim().length > 0;
    }).length;
    const accuracyText = totalAnswered === 0 ? "还没作答" : `${Math.round((totalCorrect / totalAnswered) * 100)}%`;
    containers.forEach(container => {
      const doneEl = container.querySelector("[data-stat-done]");
      const accEl = container.querySelector("[data-stat-accuracy]");
      const noteEl = container.querySelector("[data-stat-notes]");
      if (doneEl) doneEl.textContent = `${completedCount()}/7`;
      if (accEl) accEl.textContent = accuracyText;
      if (noteEl) noteEl.textContent = `${noteCount}`;
    });
  }

  function setupNotes() {
    document.querySelectorAll("[data-note]").forEach(area => {
      const key = NOTE_PREFIX + (area.dataset.note || location.pathname);
      area.value = localStorage.getItem(key) || "";
      area.addEventListener("input", () => {
        localStorage.setItem(key, area.value);
        renderHomeStats();
      });
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
        if (!confirm("清除7课完成记录、闯关答题记录、已读小节进度和本页学习勾选？笔记不会删除。")) return;
        localStorage.removeItem(KEY);
        Object.keys(localStorage)
          .filter(k => k.startsWith(STUDY_PREFIX) || k.startsWith(QUIZ_PREFIX) || k.startsWith(READ_PREFIX))
          .forEach(k => localStorage.removeItem(k));
        location.reload();
      });
    });
  }

  function setupReaderNavigation() {
    const sections = Array.from(document.querySelectorAll("[data-reader-section]"));
    const links = Array.from(document.querySelectorAll("[data-toc-link]"));
    if (!sections.length || !links.length) return;

    const linksById = new Map(links.map(link => [new URL(link.href).hash.slice(1), link]));
    const sectionText = new Map(sections.map(section => [section.id, section.textContent.toLowerCase()]));
    const lesson = document.body.dataset.lesson;
    const readKey = READ_PREFIX + lesson;
    const visited = new Set(lesson ? JSON.parse(localStorage.getItem(readKey) || "[]") : []);

    const setActive = id => {
      const active = linksById.get(id);
      links.forEach(link => link.classList.toggle("active", link === active));
      if (active && window.innerWidth <= 800) active.scrollIntoView({ block: "nearest", inline: "center" });
    };

    const renderReadCount = () => {
      document.querySelectorAll("[data-read-count]").forEach(el => {
        el.textContent = `${visited.size} / ${sections.length} 小节已读`;
      });
    };
    renderReadCount();

    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver(entries => {
        const visible = entries
          .filter(entry => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]) setActive(visible[0].target.id);
        let changed = false;
        entries.forEach(entry => {
          if (entry.isIntersecting && !visited.has(entry.target.id)) {
            visited.add(entry.target.id);
            changed = true;
          }
        });
        if (changed && lesson) {
          localStorage.setItem(readKey, JSON.stringify(Array.from(visited)));
          renderReadCount();
        }
      }, { rootMargin: "-18% 0px -62% 0px", threshold: [0, .15, .5] });
      sections.forEach(section => observer.observe(section));
    }

    const search = document.querySelector("[data-lesson-search]");
    if (search) {
      search.addEventListener("input", () => {
        const query = search.value.trim().toLowerCase();
        links.forEach(link => {
          const id = new URL(link.href).hash.slice(1);
          const haystack = `${link.textContent.toLowerCase()} ${sectionText.get(id) || ""}`;
          link.classList.toggle("search-hidden", Boolean(query) && !haystack.includes(query));
        });
      });
    }
  }

  function setupSorter() {
    document.querySelectorAll("[data-sorter]").forEach(sorter => {
      const items = Array.from(sorter.querySelectorAll("[data-sorter-item]"));
      const scoreEl = sorter.querySelector("[data-sorter-score]");
      const retryButton = sorter.querySelector("[data-sorter-retry]");

      const updateScore = () => {
        if (!scoreEl) return;
        const answered = items.filter(item => item.dataset.answered === "1");
        const correct = answered.filter(item => item.classList.contains("correct"));
        scoreEl.textContent = answered.length === items.length
          ? `完成：${correct.length} / ${items.length} 正确`
          : `已判断 ${answered.length} / ${items.length}`;
      };

      const reset = () => {
        items.forEach(item => {
          item.dataset.answered = "";
          item.classList.remove("correct", "incorrect");
          item.querySelectorAll("[data-sorter-choice]").forEach(b => b.classList.remove("chosen"));
          const feedback = item.querySelector(".sorter-feedback");
          if (feedback) feedback.textContent = "";
        });
        updateScore();
      };

      items.forEach(item => {
        const correct = item.dataset.correct;
        item.querySelectorAll("[data-sorter-choice]").forEach(button => {
          button.addEventListener("click", () => {
            if (item.dataset.answered === "1") return;
            item.dataset.answered = "1";
            const ok = button.dataset.sorterChoice === correct;
            item.classList.add(ok ? "correct" : "incorrect");
            button.classList.add("chosen");
            const feedback = item.querySelector(".sorter-feedback");
            if (feedback) feedback.textContent = ok ? "✓ 判断正确。" : `再想一步——${item.dataset.hint || "对照上面的四种性质。"}`;
            updateScore();
          });
        });
      });

      if (retryButton) retryButton.addEventListener("click", reset);
      updateScore();
    });
  }

  function setupAnnotate() {
    document.querySelectorAll("[data-annotate]").forEach(annotate => {
      const panel = annotate.querySelector("[data-annotate-panel]");
      if (!panel) return;
      annotate.querySelectorAll("[data-annotate-flag]").forEach(flag => {
        flag.addEventListener("click", () => {
          const isActive = flag.classList.contains("active");
          annotate.querySelectorAll("[data-annotate-flag]").forEach(f => f.classList.remove("active"));
          if (isActive) {
            panel.hidden = true;
            return;
          }
          flag.classList.add("active");
          panel.hidden = false;
          panel.innerHTML = `
            <p class="annotate-panel-row"><strong>为什么可疑</strong>${flag.dataset.why || ""}</p>
            <p class="annotate-panel-row"><strong>影响</strong>${flag.dataset.impact || ""}</p>
            <p class="annotate-panel-row"><strong>还不能断言</strong>${flag.dataset.limit || ""}</p>
          `;
        });
      });
    });
  }

  function setupGlossary() {
    const terms = document.querySelectorAll("[data-term]");
    if (!terms.length || !globalThis.ValuationLabGlossary) return;

    const popover = document.createElement("div");
    popover.className = "term-popover";
    popover.setAttribute("role", "tooltip");
    popover.hidden = true;
    document.body.appendChild(popover);

    let pinned = false;
    let activeTrigger = null;

    const hide = () => {
      popover.hidden = true;
      pinned = false;
      if (activeTrigger) activeTrigger.setAttribute("aria-expanded", "false");
      activeTrigger = null;
    };

    const show = trigger => {
      const entry = globalThis.ValuationLabGlossary[trigger.dataset.term];
      if (!entry) return;
      activeTrigger = trigger;
      trigger.setAttribute("aria-expanded", "true");
      popover.innerHTML = `
        <strong class="term-popover-title">${entry.term}</strong>
        <p class="term-popover-short">${entry.short}</p>
        ${entry.formula ? `<code class="term-popover-formula">${entry.formula}</code>` : ""}
        ${entry.caution ? `<p class="term-popover-caution">${entry.caution}</p>` : ""}
      `;
      popover.hidden = false;
      const rect = trigger.getBoundingClientRect();
      const width = Math.min(320, window.innerWidth - 24);
      popover.style.width = `${width}px`;
      let left = rect.left;
      if (left + width > window.innerWidth - 12) left = window.innerWidth - width - 12;
      if (left < 12) left = 12;
      const top = rect.bottom + 8;
      popover.style.left = `${left}px`;
      popover.style.top = `${top}px`;
    };

    terms.forEach(trigger => {
      trigger.setAttribute("type", "button");
      trigger.setAttribute("aria-expanded", "false");
      trigger.addEventListener("mouseenter", () => show(trigger));
      trigger.addEventListener("mouseleave", () => { if (!pinned) hide(); });
      trigger.addEventListener("focus", () => show(trigger));
      trigger.addEventListener("blur", () => { if (!pinned) hide(); });
      trigger.addEventListener("click", event => {
        event.preventDefault();
        if (pinned && activeTrigger === trigger) { hide(); return; }
        show(trigger);
        pinned = true;
      });
    });

    document.addEventListener("scroll", hide, { passive: true, capture: true });
    document.addEventListener("keydown", event => { if (event.key === "Escape") hide(); });
    document.addEventListener("click", event => {
      if (pinned && !popover.contains(event.target) && event.target !== activeTrigger) hide();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    setupQuizzes();
    setupNotes();
    setupCompletion();
    setupStudyChecks();
    setupReset();
    setupReaderNavigation();
    setupSorter();
    setupAnnotate();
    setupGlossary();
    renderProgress();
  });
})();
