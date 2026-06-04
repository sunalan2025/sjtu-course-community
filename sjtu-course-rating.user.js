// ==UserScript==
// @name         SJTU 选课社区评分助手
// @namespace    https://course.sjtu.plus
// @version      6.3.0
// @description  在交大选课页面显示教师/课程评分，悬停弹出详情窗口（含图表）
// @author       SJTU Course Community
// @match        https://i.sjtu.edu.cn/xsxk/*
// @match        https://i.sjtu.edu.cn/*
// @grant        GM_xmlhttpRequest
// @grant        GM_registerMenuCommand
// @grant        GM_getValue
// @grant        GM_setValue
// @connect      localhost
// @connect      127.0.0.1
// @connect      zeabur.app
// @connect      sjtu-course.zeabur.app
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // 注意：选课页面的 jquery.extends.contact-min.js 覆盖了 Array.prototype.filter
  // 所有 filter 操作必须使用 for 循环代替

  // ============================================================
  // 配置
  // ============================================================
  const API_BASE = GM_getValue('apiBase', 'https://sjtu-course.zeabur.app');
  const CACHE_TTL = 10 * 60 * 1000;
  const HOVER_DELAY = 400;

  // ============================================================
  // 菜单
  // ============================================================
  GM_registerMenuCommand('⚙️ 设置 API 地址', () => {
    const input = prompt('本地 API 地址', API_BASE);
    if (input !== null) {
      GM_setValue('apiBase', input.trim() || 'https://sjtu-course.zeabur.app');
      location.reload();
    }
  });

  GM_registerMenuCommand('🔄 刷新评分', () => {
    cache.clear();
    removeAllBadges();
    scanAll();
  });

  // ============================================================
  // 缓存
  // ============================================================
  const cache = new Map();
  function getCached(k) { const e = cache.get(k); return (e && Date.now() - e.ts < CACHE_TTL) ? e.data : (cache.delete(k), null); }
  function setCache(k, v) { cache.set(k, { data: v, ts: Date.now() }); }

  // ============================================================
  // API 请求封装
  // ============================================================
  function apiGet(path) {
    return new Promise((resolve, reject) => {
      const cached = getCached(path);
      if (cached) return resolve(cached);
      GM_xmlhttpRequest({
        method: 'GET', url: `${API_BASE}${path}`, timeout: 8000,
        onload: r => { try { const d = JSON.parse(r.responseText); setCache(path, d); resolve(d); } catch (e) { reject(e); } },
        onerror: reject, ontimeout: () => reject(new Error('timeout'))
      });
    });
  }

  // ============================================================
  // Chart.js iframe 隔离加载（绕过页面被破坏的 Array.prototype.filter）
  // ============================================================
  let chartIframe = null;
  let chartIframeReady = false;

  function ensureChartIframe() {
    return new Promise((resolve) => {
      if (chartIframeReady && chartIframe && chartIframe.contentWindow.Chart) {
        return resolve(chartIframe.contentWindow.Chart);
      }
      if (chartIframe) return resolve(null); // 正在加载中

      chartIframe = document.createElement('iframe');
      chartIframe.style.cssText = 'position:fixed;left:-9999px;width:400px;height:300px;border:none;';
      chartIframe.srcdoc = `<!DOCTYPE html><html><head>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"><\/script>
        </head><body></body></html>`;
      chartIframe.onload = () => {
        // 检查 Chart.js 是否加载完成
        let attempts = 0;
        const check = setInterval(() => {
          attempts++;
          if (chartIframe.contentWindow.Chart || attempts > 30) {
            clearInterval(check);
            chartIframeReady = !!chartIframe.contentWindow.Chart;
            resolve(chartIframe.contentWindow.Chart);
          }
        }, 100);
      };
      document.body.appendChild(chartIframe);
    });
  }

  async function renderChartAsImage(type, data, options, width, height) {
    const Chart = await ensureChartIframe();
    if (!Chart) return null;

    // 在 iframe 中创建临时 canvas
    const iframeDoc = chartIframe.contentDocument;
    const canvas = iframeDoc.createElement('canvas');
    canvas.width = width * 2; // 2x for retina
    canvas.height = height * 2;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    iframeDoc.body.appendChild(canvas);

    const chart = new Chart(canvas, { type, data, options: { ...options, animation: false } });

    // 等待渲染完成
    await new Promise(r => setTimeout(r, 200));

    const dataUrl = canvas.toDataURL('image/png');

    // 清理
    chart.destroy();
    iframeDoc.body.removeChild(canvas);

    return dataUrl;
  }

  // ============================================================
  // 弹出窗口管理器
  // ============================================================
  let popup = null;
  let hideTimer = null;

  function createPopup() {
    if (popup) return popup;
    popup = document.createElement('div');
    popup.id = 'sjtu-rating-popup';
    popup.style.cssText = `
      position: fixed; z-index: 99999;
      width: 420px; max-height: 560px;
      background: #fff; border-radius: 14px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.18), 0 4px 12px rgba(0,0,0,0.08);
      border: 1px solid rgba(0,0,0,0.06);
      overflow: hidden; pointer-events: auto;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      transition: opacity 0.2s ease;
    `;
    document.body.appendChild(popup);

    popup.addEventListener('mouseenter', () => clearTimeout(hideTimer));
    popup.addEventListener('mouseleave', () => scheduleHide());
    return popup;
  }

  function showPopupAt(x, y) {
    const p = createPopup();
    const pw = 420, ph = 560;
    const left = (x + pw > window.innerWidth - 16) ? x - pw - 12 : x + 12;
    const top = Math.min(y, window.innerHeight - ph - 16);
    p.style.left = `${Math.max(8, left)}px`;
    p.style.top = `${Math.max(8, top)}px`;
    p.style.opacity = '1';
    p.style.display = 'block';
  }

  function hidePopup() {
    if (popup) { popup.style.opacity = '0'; setTimeout(() => { if (popup) popup.style.display = 'none'; }, 200); }
  }

  function scheduleHide() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(hidePopup, 250);
  }

  // ============================================================
  // 渲染教师详情弹窗
  // ============================================================
  async function showTeacherPopup(name, x, y) {
    showPopupAt(x, y);
    popup.innerHTML = `
      <div style="padding:50px 16px;text-align:center;color:#6b7280;">
        <div style="display:inline-block;width:24px;height:24px;border:2.5px solid #e5e7eb;border-top-color:#0f766e;border-radius:50%;animation:sjtu-spin 0.7s linear infinite;"></div>
        <div style="margin-top:12px;font-size:13px;">正在加载 ${name} 的数据...</div>
      </div>
      <style>@keyframes sjtu-spin{to{transform:rotate(360deg)}}</style>
    `;

    try {
      const d = await apiGet(`/api/teacher_detail?name=${encodeURIComponent(name)}`);
      if (!d || d.error) {
        popup.innerHTML = `<div style="padding:50px 16px;text-align:center;color:#9ca3af;">${d?.error || '未找到数据'}</div>`;
        return;
      }

      // 使用 API 返回的加权评分
      const avgRating = d.weighted_avg;
      const totalReviews = d.total_reviews || 0;
      const courseCount = (d.courses || []).length;

      // 评分分布数据
      const distMap = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
      (d.distribution || []).forEach(r => distMap[r.rating] = r.cnt);
      const distData = [distMap[1], distMap[2], distMap[3], distMap[4], distMap[5]];

      // 学期趋势数据
      const trendLabels = (d.trend || []).map(t => t.semester.replace(/^\d{4}-\d{4}-(\d)$/, 'S$1'));
      const trendAvgs = (d.trend || []).map(t => t.avg);

      // 评分颜色
      const rc = avgRating != null ? (avgRating >= 4.5 ? '#059669' : avgRating >= 4.0 ? '#0d9488' : avgRating >= 3.5 ? '#a16207' : avgRating >= 3.0 ? '#c2410c' : '#dc2626') : '#9ca3af';
      const rbg = avgRating != null ? (avgRating >= 4.5 ? '#ecfdf5' : avgRating >= 4.0 ? '#f0fdfa' : avgRating >= 3.5 ? '#fefce8' : avgRating >= 3.0 ? '#fff7ed' : '#fef2f2') : '#f3f4f6';

      // 课程列表（仅显示有评分的，带进度条）
      const allCourses = d.courses || [];
      const ratedCourses = [];
      for (let i = 0; i < allCourses.length; i++) {
        if (allCourses[i].rating_count > 0) ratedCourses.push(allCourses[i]);
      }
      const courseHtml = ratedCourses.slice(0, 5).map(c => {
        const pct = Math.min(100, ((c.rating_avg || 0) / 5) * 100);
        const cc = c.rating_avg >= 4 ? '#059669' : c.rating_avg >= 3 ? '#a16207' : '#dc2626';
        return `
          <div style="padding:7px 0;border-bottom:1px solid #f3f4f6;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
              <div style="flex:1;min-width:0;font-size:12px;font-weight:500;color:#1f2937;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${c.name}</div>
              <div style="margin-left:8px;font-size:12px;font-weight:600;color:${cc};white-space:nowrap;">★${Number(c.rating_avg).toFixed(1)}</div>
            </div>
            <div style="display:flex;align-items:center;gap:6px;">
              <div style="flex:1;height:5px;background:#f3f4f6;border-radius:3px;overflow:hidden;">
                <div style="height:100%;width:${pct}%;background:${cc};border-radius:3px;"></div>
              </div>
              <div style="font-size:10px;color:#9ca3af;white-space:nowrap;">${c.rating_count}条</div>
            </div>
          </div>
        `;
      }).join('');

      // 最新评论（卡片式，最多3条）
      const reviewHtml = (d.recent_reviews || []).slice(0, 3).map(r => {
        const filled = Math.min(5, Math.max(0, r.rating || 0));
        const stars = '★'.repeat(filled) + '☆'.repeat(5 - filled);
        const escaped = (r.content || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return `
          <div style="padding:10px;background:#f9fafb;border-radius:8px;margin-bottom:6px;">
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;">
              <span style="font-size:12px;color:#f59e0b;letter-spacing:1px;">${stars}</span>
              <span style="font-size:10px;color:#9ca3af;">${r.semester || ''}</span>
            </div>
            <div style="font-size:12px;color:#6b7280;margin-bottom:3px;">${r.course_name || ''}</div>
            <div style="font-size:12px;color:#374151;line-height:1.6;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">${escaped}</div>
          </div>
        `;
      }).join('');

      popup.innerHTML = `
        <div style="padding:16px;overflow-y:auto;max-height:560px;" id="sjtu-popup-scroll">
          <!-- 头部 -->
          <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid #f3f4f6;">
            <div style="width:52px;height:52px;border-radius:50%;background:${rbg};display:flex;align-items:center;justify-content:center;flex-shrink:0;border:2px solid ${rc}20;">
              <span style="font-size:22px;font-weight:700;color:${rc};">${avgRating != null ? avgRating.toFixed(1) : '-'}</span>
            </div>
            <div style="flex:1;min-width:0;">
              <div style="font-size:16px;font-weight:600;color:#111827;">${d.name}</div>
              <div style="font-size:12px;color:#6b7280;margin-top:2px;">${d.department || ''} · ${d.title || ''}</div>
              <div style="font-size:11px;color:#9ca3af;margin-top:3px;">
                <span style="display:inline-block;padding:1px 6px;background:#f3f4f6;border-radius:4px;margin-right:4px;">${totalReviews} 条点评</span>
                <span style="display:inline-block;padding:1px 6px;background:#f3f4f6;border-radius:4px;">${courseCount} 门课</span>
              </div>
            </div>
          </div>

          <!-- 图表区（图片渲染，iframe 隔离） -->
          <div style="display:flex;gap:8px;margin-bottom:14px;">
            <div style="flex:1;background:#f9fafb;border-radius:10px;padding:10px;">
              <div style="font-size:11px;color:#9ca3af;margin-bottom:6px;font-weight:500;">评分分布</div>
              <div id="sjtu-dist-chart-box" style="height:100px;display:flex;align-items:center;justify-content:center;">
                <div style="width:16px;height:16px;border:2px solid #e5e7eb;border-top-color:#0f766e;border-radius:50%;animation:sjtu-spin 0.7s linear infinite;"></div>
              </div>
            </div>
            <div style="flex:1;background:#f9fafb;border-radius:10px;padding:10px;">
              <div style="font-size:11px;color:#9ca3af;margin-bottom:6px;font-weight:500;">学期趋势</div>
              <div id="sjtu-trend-chart-box" style="height:100px;display:flex;align-items:center;justify-content:center;">
                <div style="width:16px;height:16px;border:2px solid #e5e7eb;border-top-color:#0f766e;border-radius:50%;animation:sjtu-spin 0.7s linear infinite;"></div>
              </div>
            </div>
          </div>

          <!-- 课程列表 -->
          ${courseHtml ? `
            <div style="margin-bottom:14px;">
              <div style="font-size:11px;color:#9ca3af;margin-bottom:8px;font-weight:500;">📚 教授课程</div>
              ${courseHtml}
            </div>
          ` : ''}

          <!-- 最新评论 -->
          ${reviewHtml ? `
            <div>
              <div style="font-size:11px;color:#9ca3af;margin-bottom:8px;font-weight:500;">💬 最新点评</div>
              ${reviewHtml}
            </div>
          ` : ''}

          <!-- 查看更多 -->
          <div style="margin-top:14px;padding-top:12px;border-top:1px solid #f3f4f6;text-align:center;">
            <a id="sjtu-view-more" href="${API_BASE}/teacher/${d.id}" target="_blank"
               style="display:inline-block;padding:8px 24px;background:#0f766e;color:#fff;border-radius:8px;font-size:13px;font-weight:500;text-decoration:none;transition:background 0.2s;">
              📖 查看更多评价
            </a>
          </div>
        </div>
        <style>@keyframes sjtu-spin{to{transform:rotate(360deg)}}</style>
      `;

      // 防止滚轮穿透
      const scrollEl = document.getElementById('sjtu-popup-scroll');
      if (scrollEl) {
        scrollEl.addEventListener('wheel', e => e.stopPropagation(), { passive: false });
      }

      // 通过 iframe 渲染图表为图片
      const distBox = document.getElementById('sjtu-dist-chart-box');
      const trendBox = document.getElementById('sjtu-trend-chart-box');

      if (distBox) {
        const distDataUrl = await renderChartAsImage('bar', {
          labels: ['1★', '2★', '3★', '4★', '5★'],
          datasets: [{ data: distData, backgroundColor: ['#fca5a5', '#fdba74', '#fde047', '#86efac', '#5eead4'], borderRadius: 4, borderSkipped: false }]
        }, {
          plugins: { legend: { display: false } },
          scales: { x: { display: true, grid: { display: false }, ticks: { font: { size: 9 }, color: '#9ca3af' } }, y: { display: false, beginAtZero: true } }
        }, 180, 90);
        if (distDataUrl) {
          distBox.innerHTML = '<img src="' + distDataUrl + '" style="width:100%;height:100%;object-fit:contain;" />';
        } else {
          distBox.innerHTML = '<div style="font-size:11px;color:#d1d5db;">图表加载失败</div>';
        }
      }

      if (trendBox && trendLabels.length > 0) {
        const trendDataUrl = await renderChartAsImage('line', {
          labels: trendLabels,
          datasets: [{ data: trendAvgs, borderColor: '#0d9488', backgroundColor: 'rgba(13,148,136,0.08)', fill: true, tension: 0.35, pointRadius: 4, pointBackgroundColor: '#0d9488', pointBorderColor: '#fff', pointBorderWidth: 1.5, borderWidth: 2.5 }]
        }, {
          plugins: { legend: { display: false } },
          scales: { x: { display: true, grid: { display: false }, ticks: { font: { size: 8 }, color: '#9ca3af', maxRotation: 45 } }, y: { display: false, min: 1, max: 5 } }
        }, 180, 90);
        if (trendDataUrl) {
          trendBox.innerHTML = '<img src="' + trendDataUrl + '" style="width:100%;height:100%;object-fit:contain;" />';
        } else {
          trendBox.innerHTML = '<div style="font-size:11px;color:#d1d5db;">图表加载失败</div>';
        }
      }

    } catch (err) {
      console.error('[SJTU Rating] 弹窗加载失败:', err);
      popup.innerHTML = `<div style="padding:50px 16px;text-align:center;color:#ef4444;">加载失败：${err.message}</div>`;
    }
  }

  // ============================================================
  // 评分徽章
  // ============================================================
  function createBadge(rating, count, tooltip, type, id) {
    const el = document.createElement('span');
    el.className = 'sjtu-rating-badge';
    el.dataset[type] = id || '';

    if (rating != null && rating > 0) {
      const c = rating >= 4.5 ? { bg: '#ecfdf5', fg: '#059669', bd: '#a7f3d0' } :
                rating >= 4.0 ? { bg: '#f0fdfa', fg: '#0d9488', bd: '#99f6e4' } :
                rating >= 3.5 ? { bg: '#fefce8', fg: '#a16207', bd: '#fde68a' } :
                rating >= 3.0 ? { bg: '#fff7ed', fg: '#c2410c', bd: '#fed7aa' } :
                                { bg: '#fef2f2', fg: '#dc2626', bd: '#fecaca' };
      el.style.cssText = `
        display:inline-flex;align-items:center;margin-left:6px;padding:0 5px;height:18px;
        border-radius:3px;font-size:11px;font-weight:600;line-height:18px;
        background:${c.bg};color:${c.fg};border:1px solid ${c.bd};
        cursor:pointer;vertical-align:middle;
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
        transition:transform 0.15s;
      `;
      el.textContent = `★${rating}`;
      el.title = tooltip;
      el.onmouseenter = () => el.style.transform = 'scale(1.1)';
      el.onmouseleave = () => el.style.transform = 'scale(1)';
    } else {
      el.style.cssText = `
        display:inline-flex;align-items:center;margin-left:6px;padding:0 4px;height:18px;
        border-radius:3px;font-size:10px;line-height:18px;color:#cbd5e1;vertical-align:middle;
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      `;
      el.textContent = '★';
      el.title = '暂无评分';
    }

    return el;
  }

  // ============================================================
  // 从 【姓名1、姓名2】职称1、职称2 提取姓名列表
  // ============================================================
  function extractNames(text) {
    if (!text) return [];
    const m = text.trim().match(/【([^】]+)】/);
    if (m) {
      // 按 "、" 拆分多个教师名
      const parts = m[1].split(/[、,，]/);
      const result = [];
      for (let i = 0; i < parts.length; i++) {
        const s = parts[i].trim();
        if (s.length >= 2 && s.length <= 6) result.push(s);
      }
      return result;
    }
    // fallback: 纯中文名
    const t = text.trim();
    if (/^[一-龥]{2,6}$/.test(t)) return [t];
    return [];
  }

  // ============================================================
  // 扫描逻辑
  // ============================================================
  // marked 记录已处理的 (element, teacherName) 对，避免同一教师重复添加
  // 格式: "elementId_teacherName"
  let marked = new Set();
  let elementCounter = 0;

  function removeAllBadges() {
    document.querySelectorAll('.sjtu-rating-badge').forEach(el => el.remove());
    marked = new Set();
    elementCounter = 0;
  }

  async function scanAll() {
    const rows = document.querySelectorAll('tr.body_tr');
    if (rows.length === 0) return;

    // name -> [{ element, target }]
    const teacherBatch = new Map();

    rows.forEach(row => {
      const nameCell = row.querySelector('td.jsxm');
      const nameZcCell = row.querySelector('td.jsxmzc');

      let rawName = null, target = null;
      // 优先使用可见的 td.jsxmzc
      if (nameZcCell && nameZcCell.textContent.trim()) {
        rawName = nameZcCell.textContent.trim();
        target = nameZcCell;
      } else if (nameCell && nameCell.textContent.trim()) {
        rawName = nameCell.textContent.trim();
        target = nameCell;
      }

      if (!rawName || !target) return;

      // 给 element 分配唯一 ID
      if (!target._sjtuId) target._sjtuId = ++elementCounter;

      // 提取教师名（可能多个）
      const names = extractNames(rawName);
      if (names.length === 0) return;

      names.forEach(name => {
        if (!teacherBatch.has(name)) teacherBatch.set(name, []);
        teacherBatch.get(name).push({ element: target, displayName: rawName });
      });
    });

    if (teacherBatch.size === 0) return;

    console.log(`[SJTU Rating] 扫描到 ${teacherBatch.size} 位教师`);

    try {
      const ratings = await apiGet(`/api/teacher_rating?names=${encodeURIComponent([...teacherBatch.keys()].join(','))}`);

      for (const [name, entries] of teacherBatch) {
        const r = ratings[name];
        const teacherId = r?.id;
        entries.forEach(({ element }) => {
          // 用 elementId + teacherName 作为 key，同一 cell 可有多个教师徽章
          const markKey = element._sjtuId + '_' + name;
          if (marked.has(markKey)) return;
          marked.add(markKey);

          const tip = r
            ? `${name}\n${r.department || ''} · ${r.title || ''}\n${r.course_count || 0} 门课 · ${r.total_reviews || 0} 条点评`
            : `${name} · 暂无数据`;

          const badge = createBadge(r?.avg_rating, r?.total_reviews, tip, 'teacher', name);

          // 悬停事件
          let hoverTimer = null;
          badge.addEventListener('mouseenter', (e) => {
            clearTimeout(hideTimer);
            hoverTimer = setTimeout(() => showTeacherPopup(name, e.clientX, e.clientY), HOVER_DELAY);
          });
          badge.addEventListener('mouseleave', () => {
            clearTimeout(hoverTimer);
            scheduleHide();
          });

          // 点击事件：打开教师详情页
          if (teacherId) {
            badge.addEventListener('click', (e) => {
              e.preventDefault();
              e.stopPropagation();
              window.open(API_BASE + '/teacher/' + teacherId, '_blank');
            });
          }

          element.appendChild(badge);
        });
      }
    } catch (err) {
      console.error('[SJTU Rating] 查询失败:', err);
    }
  }

  // ============================================================
  // 防抖 + 监听
  // ============================================================
  let timer = null;
  function debounceScan() { if (timer) clearTimeout(timer); timer = setTimeout(scanAll, 500); }

  function watchPage() {
    new MutationObserver((mutations) => {
      for (const m of mutations) { if (m.addedNodes.length > 0) { debounceScan(); return; } }
    }).observe(document.body, { childList: true, subtree: true });
  }

  // ============================================================
  // 初始化
  // ============================================================
  function init() {
    console.log('[SJTU Rating] v5.0.0 已加载');
    // 预加载 Chart.js iframe（后台加载，不阻塞）
    ensureChartIframe();
    setTimeout(scanAll, 1500);
    watchPage();
    document.addEventListener('keydown', e => {
      if (e.ctrlKey && e.shiftKey && e.key === 'R') { e.preventDefault(); removeAllBadges(); scanAll(); }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
