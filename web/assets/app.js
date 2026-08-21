(() => {
  const KEY = "valuation-lab-progress-v1";
  const NOTE_PREFIX = "valuation-lab-note:";
  const STUDY_PREFIX = "valuation-lab-study:";
  const QUIZ_PREFIX = "valuation-lab-quiz:";
  const READ_PREFIX = "valuation-lab-read:";

  const LESSONS = [
    { id: "day-1", title: "模型到底在说什么" },
    { id: "day-2", title: "亲手打通价值桥" },
    { id: "day-3", title: "检查估值输入" },
    { id: "day-4", title: "完成最小 DCF" },
    { id: "day-5", title: "反向 DCF" },
    { id: "day-6", title: "方法适不适合" },
    { id: "day-7", title: "长飞综合练习" },
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

  function lessonPageHref(lessonId) {
    const prefix = document.body.dataset.lessonHrefPrefix || "";
    return `${prefix}${lessonId}.html`;
  }

  function bindProgressCount(label, current) {
    const targetId = current || (firstIncompleteLesson() || LESSONS[0]).id;
    const href = lessonPageHref(targetId);
    const day = targetId.replace("day-", "");
    const aria = `打开第${day}课`;
    if (label.tagName === "A") {
      label.href = href;
      label.setAttribute("aria-label", aria);
      decorateEmbeddedReferenceLink(label);
      return;
    }
    const link = document.createElement("a");
    link.className = "reader-progress-count";
    if (label.hasAttribute("data-progress-text")) {
      link.setAttribute("data-progress-text", "");
    }
    link.textContent = label.textContent;
    link.href = href;
    link.setAttribute("aria-label", aria);
    label.replaceWith(link);
    decorateEmbeddedReferenceLink(link);
  }

  function renderDayDots() {
    const containers = document.querySelectorAll("[data-day-dots]");
    if (!containers.length) return;
    const p = readProgress();
    const current = document.body.dataset.lesson;
    containers.forEach(container => {
      container.innerHTML = "";
      LESSONS.forEach((lesson, index) => {
        const day = index + 1;
        const dot = document.createElement("a");
        dot.className = "day-dot";
        dot.href = lessonPageHref(lesson.id);
        if (p[lesson.id]) dot.classList.add("done");
        if (lesson.id === current) {
          dot.classList.add("current");
          dot.setAttribute("aria-current", "page");
        }
        const status = p[lesson.id] ? " · 已完成" : "";
        dot.title = `${lesson.title}${status}`;
        dot.setAttribute("aria-label", `第${day}课：${lesson.title}${status}`);
        container.appendChild(dot);
        decorateEmbeddedReferenceLink(dot);
      });
      const progress = container.closest(".reader-course-progress");
      if (!progress) return;
      progress.setAttribute("role", "navigation");
      progress.setAttribute("aria-label", "跳转到各课");
      const label = progress.querySelector("small, .reader-progress-count");
      if (label) bindProgressCount(label, current);
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
        const prefix = document.body.dataset.lessonHrefPrefix || "";
        link.href = `${prefix}${lesson.id}.html`;
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

    const drawer = document.querySelector(".lesson-toc-drawer");
    const drawerLabel = document.querySelector("[data-toc-drawer-current]");
    const mobileToc = window.matchMedia("(max-width: 800px)");
    const syncDrawerOpen = () => {
      if (!drawer) return;
      if (!mobileToc.matches) drawer.open = true;
    };
    if (drawer) {
      mobileToc.addEventListener("change", syncDrawerOpen);
      syncDrawerOpen();
    }

    const setActive = id => {
      const active = linksById.get(id);
      links.forEach(link => link.classList.toggle("active", link === active));
      if (drawerLabel && active) {
        drawerLabel.textContent = active.textContent.trim();
      }
      if (active && mobileToc.matches) active.scrollIntoView({ block: "nearest" });
    };
    const initial = links.find(link => link.classList.contains("active")) || links[0];
    if (drawerLabel && initial) drawerLabel.textContent = initial.textContent.trim();
    links.forEach(link => {
      link.addEventListener("click", () => {
        if (drawer && mobileToc.matches) drawer.open = false;
      });
    });

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
            if (feedback) feedback.textContent = ok ? "✓ 判断正确。" : `再想一步——${item.dataset.hint || "对照上面的信息性质。"}`;
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

  function setupAgentAudit() {
    document.querySelectorAll("[data-agent-variant-tab]").forEach(tab => {
      tab.addEventListener("click", () => {
        const wanted = tab.dataset.agentVariantTab;
        document.querySelectorAll("[data-agent-variant-tab]").forEach(other => {
          other.setAttribute("aria-selected", String(other.dataset.agentVariantTab === wanted));
        });
        document.querySelectorAll("[data-agent-variant]").forEach(panel => {
          panel.hidden = panel.dataset.agentVariant !== wanted;
        });
      });
    });

    document.querySelectorAll("[data-agent-audit]").forEach(audit => {
      const issues = Array.from(audit.querySelectorAll("[data-agent-issue]"));
      const grades = Array.from(audit.querySelectorAll("[data-agent-grade]"));
      const summary = audit.querySelector("[data-agent-summary]");
      const retryButton = audit.querySelector("[data-agent-retry]");
      const expectedGrade = audit.dataset.agentAnswer || "unknown";
      let selectedGrade = "";

      // A judgement is scored three ways: correct, false alarm (a compliant clause
      // marked as a defect) and miss (a real defect waved through as compliant).
      const judged = () => issues.filter(issue => issue.dataset.judged);
      const correct = () => issues.filter(issue => issue.dataset.judged === issue.dataset.correctState);
      const falseAlarms = () => issues.filter(issue =>
        issue.dataset.correctState === "compliant" && issue.dataset.judged && issue.dataset.judged !== "compliant");
      const misses = () => issues.filter(issue =>
        issue.dataset.correctState !== "compliant" && issue.dataset.judged === "compliant");

      const gradeLabel = { usable: "可继续使用", partial: "带条件使用", unknown: "无法确认" };
      const verdictNote = {
        unknown: "关键缺口没有一条被关闭：来源无法定位、时点被穿越、内部调整无桥、派生值未复算。补齐前不能声称“已经验证”。",
        partial: "多数条款已经可追溯、可复算，只剩终值增长缺可定位证据。缺口已知且可隔离，因此限定用途继续用，而不是整份停用。"
      };

      const renderSummary = () => {
        if (!summary) return;
        const done = judged().length;
        const line = `已判断 ${done} / ${issues.length} · 正确 ${correct().length} · 误报 ${falseAlarms().length} · 漏判 ${misses().length}`;
        if (done < issues.length) {
          summary.className = "agent-audit-summary";
          summary.innerHTML = `<strong>继续判断</strong><p>${line}。判完全部条款后再选使用等级。</p>`;
          return;
        }
        if (!selectedGrade) {
          summary.className = "agent-audit-summary ready";
          summary.innerHTML = `<strong>条款判断完成</strong><p>${line}。现在选择这段输出的使用等级。</p>`;
          return;
        }
        if (selectedGrade !== expectedGrade) {
          summary.className = "agent-audit-summary incorrect";
          summary.innerHTML = `<strong>等级不成立</strong><p>${line}。这段输出的准确等级是“${gradeLabel[expectedGrade]}”：${verdictNote[expectedGrade] || ""}</p>`;
          return;
        }
        if (falseAlarms().length || misses().length) {
          summary.className = "agent-audit-summary incorrect";
          summary.innerHTML = `<strong>等级对了，判断还没对</strong><p>${line}。等级选对不能掩盖误报或漏判——一个把合规条款也标成问题的验收器，和一个全部放行的验收器同样不可用。</p>`;
          return;
        }
        summary.className = "agent-audit-summary complete";
        summary.innerHTML = `<strong>验收完成：${gradeLabel[expectedGrade]}</strong><p>${line}，没有误报和漏判。${verdictNote[expectedGrade] || ""}</p>`;
      };

      const reset = () => {
        selectedGrade = "";
        grades.forEach(grade => grade.classList.remove("chosen"));
        issues.forEach(issue => {
          delete issue.dataset.judged;
          issue.classList.remove("correct", "incorrect");
          issue.querySelectorAll("[data-agent-state]").forEach(b => b.classList.remove("chosen"));
          const feedback = issue.querySelector("[data-agent-issue-feedback]");
          if (feedback) feedback.textContent = "";
        });
        renderSummary();
      };

      issues.forEach(issue => {
        issue.querySelectorAll("[data-agent-state]").forEach(button => {
          button.addEventListener("click", () => {
            if (issue.dataset.judged) return;
            const picked = button.dataset.agentState || "";
            const expected = issue.dataset.correctState || "";
            issue.dataset.judged = picked;
            button.classList.add("chosen");
            const ok = picked === expected;
            issue.classList.add(ok ? "correct" : "incorrect");
            const feedback = issue.querySelector("[data-agent-issue-feedback]");
            if (feedback) {
              let prefix = ok ? "✓ 判断正确。" : "✗ 判断不成立。";
              if (!ok && expected === "compliant") prefix = "✗ 误报：这一条其实合规。";
              if (!ok && picked === "compliant") prefix = "✗ 漏判：这一条不能放行。";
              feedback.textContent = `${prefix}${issue.dataset.explanation || ""}`;
            }
            renderSummary();
          });
        });
      });

      grades.forEach(button => {
        button.addEventListener("click", () => {
          if (judged().length < issues.length) return;
          selectedGrade = button.dataset.agentGrade || "";
          grades.forEach(grade => grade.classList.toggle("chosen", grade === button));
          renderSummary();
        });
      });

      if (retryButton) retryButton.addEventListener("click", reset);
      renderSummary();
    });
  }

  const REFERENCE_CLOSE_MESSAGE = "valuation-lab:close-reference";

  function setupMarkdownReference() {
    const dialog = document.querySelector("[data-markdown-reference-dialog]");
    const openers = Array.from(document.querySelectorAll("[data-markdown-reference-open]"));
    if (!dialog || !openers.length) return;
    const closeButton = dialog.querySelector("[data-markdown-reference-close]");
    const frame = dialog.querySelector("[data-markdown-reference-frame]");
    let lastFocused = null;

    const setExpanded = expanded => {
      openers.forEach(opener => opener.setAttribute("aria-expanded", expanded ? "true" : "false"));
      document.documentElement.classList.toggle("markdown-reference-open", expanded);
    };

    const openDialog = opener => {
      if (dialog.open) return;
      lastFocused = opener;
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
      setExpanded(true);
      if (closeButton) closeButton.focus();
    };

    const closeDialog = () => {
      if (!dialog.open) return;
      if (typeof dialog.close === "function") dialog.close();
      else {
        dialog.removeAttribute("open");
        setExpanded(false);
        if (lastFocused) lastFocused.focus();
      }
    };

    openers.forEach(opener => opener.addEventListener("click", () => openDialog(opener)));
    if (closeButton) closeButton.addEventListener("click", closeDialog);
    dialog.querySelectorAll("[data-open-reference-window]").forEach(control => {
      control.addEventListener("click", event => {
        const href = control.getAttribute("href");
        if (!href) return;
        const url = new URL(href, window.location.href).href;
        // file:// 下每个文件都是独立源。带 noopener 时新窗口会先停在
        // about:blank，再跳到本地文件会被 Chrome 拦截，当前课页也可能被换掉。
        const opened = window.open(url, "valuation-lab-reference", "width=1100,height=900");
        if (opened) event.preventDefault();
      });
    });
    dialog.addEventListener("close", () => {
      setExpanded(false);
      if (lastFocused) lastFocused.focus();
    });
    dialog.addEventListener("click", event => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const inside = event.clientX >= rect.left && event.clientX <= rect.right
        && event.clientY >= rect.top && event.clientY <= rect.bottom;
      if (!inside) closeDialog();
    });
    document.addEventListener("keydown", event => {
      if (event.key !== "Escape" || !dialog.open) return;
      event.preventDefault();
      closeDialog();
    });
    // 抽屉里的参考章通过 postMessage 请求关闭：file:// 下父子文档同源检查不可用，只能比对 window 引用。
    window.addEventListener("message", event => {
      if (!frame || event.source !== frame.contentWindow) return;
      if (event.data !== REFERENCE_CLOSE_MESSAGE) return;
      closeDialog();
    });
  }

  function decorateEmbeddedReferenceLink(link) {
    const body = document.body;
    if (!body || !body.classList.contains("markdown-reference-page")) return;
    if (window.self === window.top) return;
    if (link.dataset.embeddedDecorated) return;

    const href = link.getAttribute("href");
    if (!href || href.startsWith("#") || /^[a-z][a-z0-9+.-]*:/i.test(href)) return;
    link.dataset.embeddedDecorated = "1";

    const prefix = body.dataset.lessonHrefPrefix || "";
    const lesson = body.dataset.lesson || "";
    const lessonHref = lesson ? `${prefix}${lesson}.html` : "";
    if (href !== lessonHref) {
      // 其余仓库文件不能在窄抽屉里打开，交给整页窗口。
      link.target = "_top";
      return;
    }
    const keepLabel = link.classList.contains("day-dot") || link.classList.contains("reader-progress-count");
    if (!keepLabel) {
      link.title = "关闭参考章，回到本课互动页";
      link.setAttribute("aria-label", "关闭参考章，回到本课互动页");
      if (!link.firstElementChild) link.textContent = "回到本课互动页";
    }
    link.addEventListener("click", event => {
      event.preventDefault();
      window.parent.postMessage(REFERENCE_CLOSE_MESSAGE, "*");
    });
  }

  function setupEmbeddedReferenceLinks() {
    document.querySelectorAll("a[href]").forEach(decorateEmbeddedReferenceLink);
  }

  function setupSourceCitations() {
    const citations = Array.from(document.querySelectorAll('a[href^="#D"]'));
    if (!citations.length) return;

    const revealSource = sourceId => {
      if (!/^D[1-7]-S\d+$/.test(sourceId)) return false;
      const target = document.getElementById(sourceId);
      if (!target) return false;
      const details = target.closest("details");
      if (details) details.open = true;
      window.requestAnimationFrame(() => target.scrollIntoView({ behavior: "smooth", block: "start" }));
      return true;
    };

    citations.forEach(citation => citation.addEventListener("click", event => {
      const sourceId = citation.getAttribute("href").slice(1);
      if (!revealSource(sourceId)) return;
      event.preventDefault();
      history.pushState(null, "", `#${sourceId}`);
    }));

    if (location.hash) revealSource(location.hash.slice(1));
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
        ${entry.expand ? `<p class="term-popover-expand">英文全称：${entry.expand}</p>` : ""}
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
    setupAgentAudit();
    setupMarkdownReference();
    setupEmbeddedReferenceLinks();
    setupSourceCitations();
    setupGlossary();
    renderProgress();
  });
})();
