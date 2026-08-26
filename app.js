(() => {
  "use strict";

  const notices = Array.isArray(window.모집공고Data) ? window.모집공고Data : [];
  const cards = document.querySelector("#category-cards");
  const list = document.querySelector("#notice-list");
  const keyword = document.querySelector("#keyword");
  const resultCount = document.querySelector("#result-count");
  const emptyState = document.querySelector("#empty-state");
  const clearButton = document.querySelector("#clear-search");

  const number = new Intl.NumberFormat("ko-KR");
  const summary = notices.reduce((acc, notice) => {
    const category = notice.분야 || "미분류";
    acc[category] ??= { count: 0, people: 0 };
    acc[category].count += 1;
    acc[category].people += Number(notice.모집인원) || 0;
    return acc;
  }, {});

  const totalPeople = notices.reduce((sum, notice) => sum + (Number(notice.모집인원) || 0), 0);
  document.querySelector("#total-posts").textContent = `${number.format(notices.length)}건`;
  document.querySelector("#total-people").textContent = `${number.format(totalPeople)}명`;
  document.querySelector("#total-categories").textContent = `${number.format(Object.keys(summary).length)}개`;

  Object.entries(summary)
    .sort(([a], [b]) => a.localeCompare(b, "ko"))
    .forEach(([category, values], index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "category-card";
      button.style.setProperty("--delay", `${index * 45}ms`);
      button.innerHTML = `
        <span class="category-card__name">${escapeHtml(category)}</span>
        <span class="category-card__metric"><strong>${number.format(values.count)}</strong>건의 공고</span>
        <span class="category-card__people">총 ${number.format(values.people)}명 모집</span>`;
      button.addEventListener("click", () => {
        keyword.value = category;
        render(category);
        keyword.focus();
      });
      cards.append(button);
    });

  function escapeHtml(value) {
    const span = document.createElement("span");
    span.textContent = String(value ?? "");
    return span.innerHTML;
  }

  function render(query = "") {
    const normalized = query.trim().toLocaleLowerCase("ko-KR");
    const filtered = notices.filter((notice) => {
      if (!normalized) return true;
      return [notice.분야, notice.지역]
        .some((value) => String(value ?? "").toLocaleLowerCase("ko-KR").includes(normalized));
    });

    list.replaceChildren();
    filtered.forEach((notice) => {
      const article = document.createElement("article");
      article.className = "notice-card";
      article.innerHTML = `
        <div class="notice-card__top">
          <span class="badge">${escapeHtml(notice.분야)}</span>
          <span class="region">${escapeHtml(notice.지역)}</span>
        </div>
        <h3>${escapeHtml(notice.프로그램명)}</h3>
        <dl>
          <div><dt>모집인원</dt><dd>${number.format(Number(notice.모집인원) || 0)}명</dd></div>
          <div><dt>활동요일</dt><dd>${escapeHtml(notice.활동요일)}요일</dd></div>
          <div><dt>마감일</dt><dd>${escapeHtml(notice.마감일)}</dd></div>
        </dl>
        <p class="notice-card__status">${escapeHtml(notice.상태)}</p>`;
      list.append(article);
    });

    resultCount.textContent = normalized
      ? `“${query.trim()}” 검색 결과 ${number.format(filtered.length)}건`
      : `전체 ${number.format(filtered.length)}건`;
    emptyState.hidden = filtered.length !== 0;
  }

  keyword.addEventListener("input", (event) => render(event.target.value));
  clearButton.addEventListener("click", () => {
    keyword.value = "";
    render();
    keyword.focus();
  });

  render();
})();
