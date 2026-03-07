<template>
  <div class="min-h-screen flex bg-gradient-to-br from-gray-50 via-indigo-50/40 to-white font-sans">
    <div class="flex-1 pt-14 pb-8 px-4 sm:px-6 lg:px-8">
      <header class="sticky top-0 z-10 -mx-4 sm:-mx-6 px-4 sm:px-6 py-3 bg-white/80 backdrop-blur border-b border-gray-200 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 class="text-xl font-semibold text-gray-800">考纲管理</h1>
          <p class="mt-1 text-sm text-gray-500">管理省份 / 专业下的考纲大类与一级知识点，支持文本与 Excel 导入、导出和批量整理。</p>
        </div>
        <div class="grid grid-cols-2 sm:flex sm:flex-wrap items-center gap-2">
          <button class="btn-primary h-9 px-4 text-sm" @click="openImport">导入考纲</button>
          <button class="btn-secondary h-9 px-4 text-sm" :disabled="!state.province||!state.major" @click="loadList">刷新数据</button>
          <button class="btn-secondary h-9 px-4 text-sm" @click="downloadTemplate">文本模板</button>
          <button class="btn-secondary h-9 px-4 text-sm" @click="downloadExcelTemplate">Excel 模板</button>
          <button class="btn-secondary h-9 px-4 text-sm" :disabled="!state.province||!state.major" @click="exportExcel">导出 Excel</button>
          <button class="btn-secondary h-9 px-4 text-sm" :disabled="!state.province||!state.major" @click="exportMarkdown">导出 Markdown</button>
        </div>
      </header>

      <section class="mt-4 grid gap-3 md:grid-cols-3">
        <article class="info-bar px-4 py-4">
          <div class="text-[11px] font-medium uppercase tracking-wide text-gray-500">当前范围</div>
          <div class="mt-2 text-lg font-semibold text-gray-800 leading-tight">{{ state.province || '未选择省份' }}</div>
          <div class="mt-1 text-sm text-gray-500 leading-5">{{ state.major || '请选择专业后开始管理' }}</div>
        </article>
        <article class="info-bar px-4 py-4">
          <div class="text-[11px] font-medium uppercase tracking-wide text-gray-500">条目概览</div>
          <div class="mt-2 flex items-end gap-2">
            <span class="text-2xl font-semibold text-gray-800 leading-none">{{ total }}</span>
            <span class="pb-0.5 text-xs text-gray-500">当前筛选结果</span>
          </div>
          <div class="mt-1.5 text-sm text-gray-500">大类 {{ kpList.length }} 个，分页 {{ state.pageSize }} 条 / 页</div>
        </article>
        <article class="info-bar px-4 py-4">
          <div class="text-[11px] font-medium uppercase tracking-wide text-gray-500">导入状态</div>
          <div class="mt-2 text-sm font-semibold leading-5" :class="importMsg ? (importOk ? 'text-emerald-600' : 'text-red-600') : 'text-gray-800'">{{ importMsg || '可直接导入文本或 Excel 模板' }}</div>
          <div class="mt-1.5 text-sm text-gray-500 leading-5">{{ importDetailLines[0] || '导入完成后会自动刷新当前范围数据。' }}</div>
        </article>
      </section>

      <section class="mt-4">
        <div class="info-bar p-4">
          <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div class="text-sm font-semibold text-gray-800">范围与筛选</div>
              <p class="mt-1 text-xs text-gray-500">先确定省份和专业，再按考纲大类或关键词过滤当前条目。</p>
            </div>
            <div class="flex flex-wrap items-center gap-2 text-xs text-gray-500">
              <span class="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-1 text-primary">共 {{ total }} 条</span>
              <span v-if="state.province && state.major" class="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-1 text-gray-600">{{ state.province }} / {{ state.major }}</span>
            </div>
          </div>

          <div class="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
            <section class="rounded-2xl border border-gray-200 bg-gray-50/60 p-4">
              <div class="text-sm font-medium text-gray-800">① 选择管理范围</div>
              <p class="mt-1 text-xs text-gray-500">范围确定后，下方列表与导入目标会同步刷新。</p>
              <div class="mt-3 grid gap-3 sm:grid-cols-2">
                <label class="block">
                  <span class="mb-1.5 block text-sm text-gray-700">省份</span>
                  <select v-if="provinces.length" v-model="state.province" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm">
                    <option v-for="p in provinces" :key="p" :value="p">{{ p }}</option>
                  </select>
                  <input v-else v-model="state.province" placeholder="如 四川省" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm"/>
                </label>
                <label class="block">
                  <span class="mb-1.5 block text-sm text-gray-700">专业</span>
                  <select v-if="majorOptions.length" v-model="state.major" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm">
                    <option v-for="m in majorOptions" :key="m" :value="m">{{ m }}</option>
                  </select>
                  <input v-else v-model="state.major" placeholder="如 计算机类" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm"/>
                </label>
              </div>
            </section>

            <section class="rounded-2xl border border-gray-200 bg-gray-50/60 p-4">
              <div class="text-sm font-medium text-gray-800">② 条件筛选</div>
              <p class="mt-1 text-xs text-gray-500">支持关键词过滤和分页密度控制。</p>
              <div class="mt-3 grid gap-3">
                <label class="block">
                  <span class="mb-1.5 block text-sm text-gray-700">搜索一级知识点</span>
                  <input v-model.trim="filters.keyword" @keyup.enter="loadList" placeholder="输入关键词后回车" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm"/>
                </label>
                <div class="grid gap-3 sm:grid-cols-[180px_minmax(0,1fr)] sm:items-end">
                  <label class="block">
                    <span class="mb-1.5 block text-sm text-gray-700">每页条数</span>
                    <select v-model.number="state.pageSize" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm">
                      <option :value="10">10</option>
                      <option :value="20">20</option>
                      <option :value="50">50</option>
                    </select>
                  </label>
                  <div class="grid grid-cols-2 gap-2 sm:justify-self-end sm:w-[220px]">
                    <button class="btn-secondary h-10 px-3 text-sm" @click="resetFilters">重置</button>
                    <button class="btn-secondary h-10 px-3 text-sm" @click="loadList">查询</button>
                  </div>
                </div>
              </div>
            </section>
          </div>

          <div class="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(340px,1fr)]">
            <section class="rounded-2xl border border-dashed border-gray-200 bg-gray-50/80 p-4">
              <div class="flex items-center justify-between gap-2">
                <div>
                  <div class="text-sm font-medium text-gray-800">③ 按大类查看</div>
                  <p class="mt-1 text-xs text-gray-500">快速切换当前专业下的考纲大类，便于聚焦编辑。</p>
                </div>
                <span class="text-xs text-gray-500">切换后自动刷新列表</span>
              </div>
              <div class="mt-3 flex flex-wrap items-start gap-2 content-start">
                <button class="inline-flex h-8 items-center rounded-full border px-3 text-xs transition" :class="!filters.kp ? 'bg-primary/10 text-primary border-primary/30' : 'bg-white text-gray-700 border-gray-300'" @click="setKP('')">全部</button>
                <button v-for="k in kpList" :key="k" class="inline-flex h-8 items-center rounded-full border px-3 text-xs transition" :class="filters.kp===k ? 'bg-primary/10 text-primary border-primary/30' : 'bg-white text-gray-700 border-gray-300'" @click="setKP(k)">
                  {{ k }}
                  <span class="ml-1 text-[10px] text-gray-500">{{ kpCounts[k]||0 }}</span>
                </button>
              </div>
              <div v-if="!kpList.length" class="mt-3 text-xs text-gray-400">当前范围暂无考纲大类</div>
            </section>

            <section class="rounded-2xl border border-gray-200 bg-white p-4">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <div class="text-sm font-medium text-gray-800">④ 当前范围操作</div>
                  <p class="mt-1 text-xs text-gray-500">保留当前范围相关的必要整理操作，不再拆成独立侧栏。</p>
                </div>
                <span class="inline-flex items-center rounded-full bg-amber-50 px-2 py-1 text-[11px] text-amber-700 border border-amber-200">{{ importMode === 'replace' ? '替换模式' : '追加模式' }}</span>
              </div>
              <div class="mt-3 grid gap-3">
                <div>
                  <label class="mb-1.5 block text-sm text-gray-700">导入模式</label>
                  <select v-model="importMode" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm">
                    <option value="replace">替换（清空后导入）</option>
                    <option value="append">追加</option>
                  </select>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button class="btn-secondary h-9 px-3 text-sm" :disabled="!state.province||!state.major" @click="dedupeDry">重复检查</button>
                  <button class="btn-secondary h-9 px-3 text-sm" :disabled="!state.province||!state.major" @click="dedupeRun">执行去重</button>
                  <button class="btn-secondary h-9 px-3 text-sm border-red-300 text-red-600 hover:bg-red-50" :disabled="!state.province||!state.major" @click="clearAll">清空当前专业</button>
                </div>
                <div v-if="opMsg" class="rounded-xl border px-3 py-2 text-xs" :class="opOk ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-red-50 text-red-700 border-red-200'">{{ opMsg }}</div>
              </div>
            </section>
          </div>
        </div>
      </section>

      <section class="mt-4 info-bar p-4">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div class="xl:w-56">
            <div class="text-sm font-semibold text-gray-800">新增条目与大类维护</div>
            <p class="mt-1 text-xs text-gray-500">补录单条考纲、重命名大类或清空当前筛选大类。</p>
          </div>
          <div class="flex-1 grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.9fr)]">
            <div class="rounded-2xl border border-gray-200 bg-gray-50/60 p-4">
              <div class="text-sm font-medium text-gray-800">新增条目</div>
              <div class="mt-3 grid gap-2 md:grid-cols-[160px_minmax(0,1fr)_auto] md:items-end">
                <input v-model.trim="createForm.kp" placeholder="考纲大类，如 计算机基础" class="h-10 rounded-xl border border-gray-300 bg-white px-3 text-sm"/>
                <input v-model.trim="createForm.primary" placeholder="一级知识点条目" class="h-10 rounded-xl border border-gray-300 bg-white px-3 text-sm"/>
                <div class="flex gap-2">
                  <button class="btn-primary h-10 px-4 text-sm flex-1" :disabled="!canCreate" @click="createItem">保存</button>
                  <button v-if="filters.kp" class="btn-secondary h-10 px-4 text-sm flex-1" @click="clearByKP(filters.kp)">清空该大类</button>
                </div>
              </div>
            </div>

            <div class="rounded-2xl border border-gray-200 bg-gray-50/60 p-4">
              <div class="text-sm font-medium text-gray-800">大类重命名</div>
              <div class="mt-3 grid gap-2">
                <input v-model.trim="renameFrom" placeholder="原大类名" class="h-10 rounded-xl border border-gray-300 bg-white px-3 text-sm"/>
                <input v-model.trim="renameTo" placeholder="新大类名" class="h-10 rounded-xl border border-gray-300 bg-white px-3 text-sm"/>
                <button class="btn-secondary h-10 px-4 text-sm" :disabled="!canRename" @click="renameKp">执行重命名</button>
              </div>
              <div v-if="renameMsg" class="mt-2 text-xs" :class="renameOk ? 'text-emerald-600' : 'text-red-600'">{{ renameMsg }}</div>
            </div>
          </div>
        </div>
      </section>

      <section class="mt-4 info-bar overflow-hidden">
        <div class="border-b border-gray-200 px-4 py-3 flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div class="text-sm font-semibold text-gray-800">条目列表</div>
            <p class="mt-1 text-xs text-gray-500">
              当前显示
              <span class="font-medium text-gray-700">{{ state.province || '未选择省份' }}</span>
              <span class="mx-1">/</span>
              <span class="font-medium text-gray-700">{{ state.major || '未选择专业' }}</span>
              <span v-if="filters.kp" class="ml-2 inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-primary">{{ filters.kp }}</span>
              <span v-if="filters.keyword" class="ml-2 text-gray-500">关键词：{{ filters.keyword }}</span>
            </p>
          </div>
          <div class="text-xs text-gray-500">支持行内修改，保存后将自动刷新列表统计。</div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full min-w-[720px] text-sm">
            <thead>
              <tr class="bg-primary/5 text-gray-600">
                <th class="py-3 px-4 text-left w-56">考纲大类</th>
                <th class="py-3 px-4 text-left">一级知识点</th>
                <th class="py-3 px-4 text-left w-40">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="it in items" :key="it.id" class="hover:bg-primary/5 align-top">
                <td class="py-2.5 px-4"><input v-model="it.kp" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm"/></td>
                <td class="py-2.5 px-4"><input v-model="it.primary" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm"/></td>
                <td class="py-2.5 px-4">
                  <div class="flex items-center gap-2">
                    <button class="btn-secondary h-9 px-3 text-sm" @click="saveItem(it)">保存</button>
                    <button class="btn-secondary h-9 px-3 text-sm" @click="deleteItem(it)">删除</button>
                  </div>
                </td>
              </tr>
              <tr v-if="!items.length">
                <td colspan="3" class="px-4 py-10 text-center">
                  <div class="mx-auto max-w-sm rounded-2xl border border-dashed border-gray-200 bg-gray-50/70 px-5 py-6">
                    <div class="text-sm font-medium text-gray-600">暂无匹配数据</div>
                    <p class="mt-1 text-xs text-gray-500">可以调整筛选条件，或通过上方导入功能批量导入考纲。</p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="px-4 py-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-t border-gray-200">
          <span class="text-xs text-gray-500">共 {{ total }} 条 · 第 {{ state.page }} 页</span>
          <div class="flex items-center gap-2">
            <button class="btn-secondary h-9 px-3 text-sm" :disabled="state.page<=1" @click="state.page--; loadList()">上一页</button>
            <button class="btn-secondary h-9 px-3 text-sm" :disabled="state.page*state.pageSize>=total" @click="state.page++; loadList()">下一页</button>
          </div>
        </div>
      </section>

      <div v-if="showImport" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4 py-4">
        <div class="w-full max-w-[1120px] rounded-3xl bg-white shadow-xl border border-gray-200 overflow-hidden">
          <div class="border-b border-gray-200 px-4 py-3 flex items-start justify-between gap-3">
            <div>
              <div class="text-base font-semibold text-gray-800">考纲导入</div>
              <p class="mt-1 text-xs text-gray-500">导入目标：{{ importTargetText }}</p>
            </div>
            <button class="inline-flex h-8 w-8 items-center justify-center rounded-full text-gray-500 hover:bg-gray-100 hover:text-gray-800 text-xl leading-none" @click="closeImport">×</button>
          </div>

          <div class="px-4 py-4">
            <div class="grid gap-4 xl:grid-cols-[minmax(0,1.55fr)_320px]">
              <section class="space-y-3">
                <div class="rounded-2xl border border-gray-200 bg-gray-50/70 p-3">
                  <div class="grid gap-3 md:grid-cols-3">
                    <label class="block">
                      <span class="mb-1.5 block text-sm text-gray-700">省份</span>
                      <input v-model.trim="importForm.province" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm"/>
                    </label>
                    <label class="block">
                      <span class="mb-1.5 block text-sm text-gray-700">专业</span>
                      <input v-model.trim="importForm.major" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm"/>
                    </label>
                    <label class="block">
                      <span class="mb-1.5 block text-sm text-gray-700">导入模式</span>
                      <select v-model="importMode" class="h-10 w-full rounded-xl border border-gray-300 bg-white px-3 text-sm">
                        <option value="replace">替换（清空后导入）</option>
                        <option value="append">追加</option>
                      </select>
                    </label>
                  </div>
                  <div class="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                    <span class="inline-flex items-center rounded-full bg-white px-3 py-1 border border-gray-200">导入目标：{{ importTargetText }}</span>
                    <span class="inline-flex items-center rounded-full px-3 py-1" :class="importMode === 'replace' ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'">
                      {{ importMode === 'replace' ? '替换模式' : '追加模式' }}
                    </span>
                  </div>
                </div>

                <div class="flex flex-wrap gap-2 rounded-2xl bg-gray-100 p-1">
                  <button class="inline-flex h-9 flex-1 items-center justify-center min-w-[140px] rounded-xl px-4 text-sm font-medium transition" :class="importTab==='text' ? 'bg-white text-primary shadow-sm' : 'text-gray-600'" @click="importTab='text'">文本导入</button>
                  <button class="inline-flex h-9 flex-1 items-center justify-center min-w-[140px] rounded-xl px-4 text-sm font-medium transition" :class="importTab==='excel' ? 'bg-white text-primary shadow-sm' : 'text-gray-600'" @click="importTab='excel'">Excel 导入</button>
                </div>

                <div v-if="importTab==='text'" class="rounded-2xl border border-gray-200 bg-white p-4 space-y-3">
                  <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div class="text-sm font-semibold text-gray-800">文本粘贴导入</div>
                      <p class="mt-1 text-xs text-gray-500">适合从文档中快速粘贴整理后的考纲内容。</p>
                    </div>
                    <div class="text-xs text-gray-500">识别格式：<code>【大类】</code> + <code>1. 内容</code></div>
                  </div>
                  <textarea v-model="importText" rows="12" placeholder="在此粘贴考纲文本：\n【计算机基础】\n1. 了解计算机的发展、特点、分类及应用领域\n2. 了解计算机的工作原理，熟悉计算机系统的组成" class="w-full rounded-2xl border border-gray-300 bg-white px-4 py-3 text-sm leading-6"></textarea>
                  <div class="flex flex-wrap items-center gap-2">
                    <button class="btn-primary h-10 px-4 text-sm" :disabled="!canSubmitTextImport || importSubmitting" @click="submitImport">
                      {{ importSubmitting ? '导入中...' : '提交文本导入' }}
                    </button>
                    <button class="btn-secondary h-10 px-4 text-sm" @click="fillImportTemplate">填入示例</button>
                    <button class="btn-secondary h-10 px-4 text-sm" @click="importText=''">清空文本</button>
                  </div>
                </div>

                <div v-else class="rounded-2xl border border-gray-200 bg-white p-4 space-y-3">
                  <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div class="text-sm font-semibold text-gray-800">Excel 批量导入</div>
                      <p class="mt-1 text-xs text-gray-500">适合整理好的模板文件，支持按行批量导入并反馈错误行。</p>
                    </div>
                    <div class="text-xs text-gray-500">支持 .xlsx / .xls，大小不超过 10MB</div>
                  </div>
                  <div class="rounded-2xl border border-dashed border-gray-300 bg-gray-50/70 px-5 py-7 text-center">
                    <div class="text-sm font-medium text-gray-700">选择 Excel 文件</div>
                    <p class="mt-1 text-xs text-gray-500">推荐先下载模板填写后再导入，未填写省份/专业列时会使用当前导入目标。</p>
                    <div class="mt-4 flex flex-wrap items-center justify-center gap-2">
                      <button class="btn-primary h-10 px-4 text-sm" :disabled="importSubmitting || !canUseImportTarget" @click="triggerExcel">{{ importSubmitting ? '上传中...' : '选择文件并导入' }}</button>
                      <button class="btn-secondary h-10 px-4 text-sm" @click="downloadExcelTemplate">下载 Excel 模板</button>
                    </div>
                    <div v-if="importExcelName" class="mt-3 text-xs text-gray-600">最近选择：{{ importExcelName }}</div>
                  </div>
                </div>
              </section>

              <aside class="space-y-3">
                <div class="rounded-2xl border border-gray-200 bg-gray-50/70 p-4">
                  <div class="text-sm font-semibold text-gray-800">导入前预检</div>
                  <ul class="mt-3 space-y-2 text-xs text-gray-600">
                    <li class="flex items-start gap-2"><span class="mt-0.5 h-1.5 w-1.5 rounded-full bg-primary"></span><span>请先确认导入目标省份、专业是否正确。</span></li>
                    <li class="flex items-start gap-2"><span class="mt-0.5 h-1.5 w-1.5 rounded-full bg-primary"></span><span>文本格式需使用 <code>【大类】</code> 和 <code>1. 内容</code>/<code>1、内容</code>。</span></li>
                    <li class="flex items-start gap-2"><span class="mt-0.5 h-1.5 w-1.5 rounded-full bg-primary"></span><span>Excel 至少需要“考纲大类 / 一级知识点”列，未带省份/专业列时会使用当前导入目标。</span></li>
                    <li class="flex items-start gap-2"><span class="mt-0.5 h-1.5 w-1.5 rounded-full bg-primary"></span><span>替换模式会先清空当前范围内已有条目，请谨慎操作。</span></li>
                  </ul>
                </div>

                <div class="rounded-2xl border border-gray-200 bg-white p-4">
                  <div class="text-sm font-semibold text-gray-800">当前导入状态</div>
                  <div class="mt-3 grid gap-2 text-xs text-gray-600">
                    <div class="flex items-center justify-between rounded-xl bg-gray-50 px-3 py-2"><span>目标范围</span><span class="font-medium text-gray-700">{{ importTargetText }}</span></div>
                    <div class="flex items-center justify-between rounded-xl bg-gray-50 px-3 py-2"><span>导入方式</span><span class="font-medium text-gray-700">{{ importTab === 'text' ? '文本粘贴' : 'Excel 文件' }}</span></div>
                    <div class="flex items-center justify-between rounded-xl bg-gray-50 px-3 py-2"><span>是否可提交</span><span class="font-medium" :class="canUseImportTarget ? 'text-emerald-600' : 'text-amber-600'">{{ canUseImportTarget ? '已设置目标' : '待补充目标' }}</span></div>
                  </div>
                </div>

                <div v-if="importTab==='text' && (importPreview.lines || importPreview.sections || importPreview.items || importPreview.invalidLines.length)" class="rounded-2xl border border-gray-200 bg-white p-4">
                  <div class="text-sm font-semibold text-gray-800">文本预检结果</div>
                  <div class="mt-3 grid grid-cols-3 gap-2 text-xs">
                    <div class="rounded-xl bg-primary/5 px-3 py-2 text-center text-gray-700">{{ importPreview.lines }}<div class="mt-1 text-[11px] text-gray-500">有效行</div></div>
                    <div class="rounded-xl bg-primary/5 px-3 py-2 text-center text-gray-700">{{ importPreview.sections }}<div class="mt-1 text-[11px] text-gray-500">大类段落</div></div>
                    <div class="rounded-xl bg-primary/5 px-3 py-2 text-center text-gray-700">{{ importPreview.items }}<div class="mt-1 text-[11px] text-gray-500">条目数</div></div>
                  </div>
                  <div v-if="importPreview.invalidLines.length" class="mt-3 text-xs text-amber-700 leading-5">未识别行：{{ importPreview.invalidLines.slice(0, 5).join('、') }}<span v-if="importPreview.invalidLines.length>5"> 等 {{ importPreview.invalidLines.length }} 行</span></div>
                </div>

                <div v-if="importMsg || importDetailLines.length" class="rounded-2xl px-4 py-3 text-xs border" :class="importOk ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-red-50 text-red-700 border-red-200'">
                  <div class="font-medium">{{ importMsg }}</div>
                  <ul v-if="importDetailLines.length" class="mt-2 space-y-1 list-disc list-inside leading-5">
                    <li v-for="line in importDetailLines" :key="line">{{ line }}</li>
                  </ul>
                </div>
              </aside>
            </div>
          </div>

          <input ref="excelInput" type="file" accept=".xlsx,.xls" class="hidden" @change="onExcelChange" />
          <div class="border-t border-gray-200 px-4 py-3 flex items-center justify-between gap-3">
            <span class="text-xs text-gray-500">导入完成后会自动刷新当前列表与大类统计。</span>
            <button class="btn-secondary h-9 px-4 text-sm" @click="closeImport">关闭</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { apiSyllabusPresets, apiManageSyllabusList, apiManageSyllabusSave, apiManageSyllabusDelete, apiManageSyllabusClear, apiManageSyllabusImportText, apiManageSyllabusExport, apiManageSyllabusTemplate, apiManageSyllabusDedupe, apiManageSyllabusRenameKp, apiManageSyllabusTemplateExcel, apiManageSyllabusImportExcel } from '../../api/index'

const provinces = ref([])
const majorsByProvince = ref({})
const state = reactive({ province: '', major: '', page: 1, pageSize: 20 })
const filters = reactive({ kp: '', keyword: '' })
const kpList = ref([])
const kpCounts = reactive({})
const items = ref([])
const total = ref(0)

const createForm = reactive({ kp: '', primary: '' })
const canCreate = computed(() => !!(state.province && state.major && createForm.kp && createForm.primary))

const showImport = ref(false)
const importMode = ref('replace')
const importTab = ref('text')
const importText = ref('')
const importMsg = ref('')
const importOk = ref(false)
const importDetailLines = ref([])
const importSubmitting = ref(false)
const importExcelName = ref('')
const importForm = reactive({ province: '', major: '' })

const opMsg = ref('')
const opOk = ref(false)
const renameFrom = ref('')
const renameTo = ref('')
const renameMsg = ref('')
const renameOk = ref(false)
const canRename = computed(() => !!(state.province && state.major && renameFrom.value && renameTo.value && renameFrom.value !== renameTo.value))

const majorOptions = computed(() => {
  const arr = majorsByProvince.value[state.province] || []
  return Array.isArray(arr) ? arr : []
})

const canUseImportTarget = computed(() => !!(importForm.province && importForm.major))
const canSubmitTextImport = computed(() => canUseImportTarget.value && !!importText.value.trim() && importPreview.value.sections > 0 && importPreview.value.items > 0)
const importTargetText = computed(() => `${importForm.province || '未设置省份'} / ${importForm.major || '未设置专业'}`)
const importPreview = computed(() => analyzeImportText(importText.value))

function analyzeImportText(text){
  const lines = String(text || '').split(/\r?\n/)
  let sections = 0
  let itemsCount = 0
  let validLines = 0
  let currentKp = ''
  const invalidLines = []
  lines.forEach((raw, idx) => {
    const s = String(raw || '').trim()
    if (!s) return
    validLines += 1
    const sectionMatch = s.match(/^【(.+?)】$/)
    if (sectionMatch){
      currentKp = sectionMatch[1].trim()
      sections += 1
      return
    }
    const isItem = /^(\d+)[.、]\s*(.+)$/.test(s)
    if (isItem && currentKp){
      itemsCount += 1
      return
    }
    invalidLines.push(idx + 1)
  })
  return { lines: validLines, sections, items: itemsCount, invalidLines }
}

function setKP(k){ filters.kp = k; state.page = 1; loadList() }
function resetFilters(){ filters.kp = ''; filters.keyword = ''; state.page = 1; loadList() }
function fillImportTemplate(){
  importText.value = ['【计算机基础】','1. 了解计算机的发展、特点、分类及应用领域','2. 了解计算机的工作原理，熟悉计算机系统的组成','','【数据库基础】','1. 了解数据、数据库、数据库系统及数据库管理系统等概念'].join('\n')
}
function clearImportFeedback(){ importMsg.value = ''; importOk.value = false; importDetailLines.value = [] }
function syncImportForm(){ importForm.province = state.province || ''; importForm.major = state.major || '' }
function openImport(tab = 'text'){ importTab.value = tab; syncImportForm(); clearImportFeedback(); showImport.value = true }
function closeImport(){ showImport.value = false; importSubmitting.value = false }

async function submitImport(){
  clearImportFeedback()
  const preview = importPreview.value
  if (!canUseImportTarget.value){ importOk.value = false; importMsg.value = '请先填写导入目标的省份和专业'; return }
  if (!importText.value.trim()){ importOk.value = false; importMsg.value = '请先粘贴要导入的文本'; return }
  if (preview.sections <= 0 || preview.items <= 0){ importOk.value = false; importMsg.value = '文本格式不完整，请至少包含一个【大类】和对应条目'; return }
  importSubmitting.value = true
  try{
    const { data } = await apiManageSyllabusImportText({ province: importForm.province, major: importForm.major, text: importText.value, mode: importMode.value })
    if (data?.success){
      importOk.value = true
      importMsg.value = '文本导入完成'
      importDetailLines.value = [
        `新增 ${data.created || 0} 条`,
        `跳过重复 ${data.skipped || 0} 条`,
        `识别大类 ${data.kp_sections || 0} 个`,
        `模式：${data.mode === 'replace' ? '替换' : '追加'}`
      ]
      state.province = importForm.province
      state.major = importForm.major
      await loadMeta(); await loadList()
    }
    else {
      importOk.value = false
      importMsg.value = data?.error_msg || '导入失败'
    }
  }catch{
    importOk.value = false
    importMsg.value = '导入异常'
  }finally{
    importSubmitting.value = false
  }
}

async function clearAll(){
  if (!state.province || !state.major) return
  try{ await apiManageSyllabusClear({ province: state.province, major: state.major }); opOk.value = true; opMsg.value = '已清空当前专业下的考纲条目'; await loadList() }catch{ opOk.value = false; opMsg.value = '清空失败' }
}
async function clearByKP(kp){
  try{ await apiManageSyllabusClear({ province: state.province, major: state.major, kp }); opOk.value = true; opMsg.value = `已清空大类“${kp}”`; await loadList() }catch{ opOk.value = false; opMsg.value = '清空大类失败' }
}
async function createItem(){
  if (!canCreate.value) return
  try{
    await apiManageSyllabusSave({ province: state.province, major: state.major, kp: createForm.kp, primary: createForm.primary })
    createForm.kp = ''; createForm.primary = ''; opOk.value = true; opMsg.value = '条目已保存'; await loadList()
  }catch{ opOk.value = false; opMsg.value = '保存失败' }
}
async function saveItem(it){
  try{ await apiManageSyllabusSave({ id: it.id, province: state.province, major: state.major, kp: it.kp, primary: it.primary }); opOk.value = true; opMsg.value = '条目已更新'; await loadList() }catch{ opOk.value = false; opMsg.value = '更新失败' }
}
async function deleteItem(it){
  try{ await apiManageSyllabusDelete({ id: it.id }); opOk.value = true; opMsg.value = '条目已删除'; await loadList() }catch{ opOk.value = false; opMsg.value = '删除失败' }
}

async function loadMeta(){
  try{
    const { data } = await apiSyllabusPresets()
    if (data?.success){ provinces.value = data.provinces || []; majorsByProvince.value = data.majors_by_province || {} }
    if (!state.province && provinces.value.length) state.province = provinces.value[0]
    if (!state.major && majorsByProvince.value[state.province] && majorsByProvince.value[state.province].length){ state.major = majorsByProvince.value[state.province][0] }
  }catch{}
}

async function loadList(){
  if (!state.province || !state.major){ items.value = []; total.value = 0; kpList.value = []; return }
  try{
    const { data } = await apiManageSyllabusList({ province: state.province, major: state.major, kp: filters.kp || undefined, q: filters.keyword || undefined, page: state.page, page_size: state.pageSize })
    if (data?.success){
      items.value = data.items || []
      total.value = data.total || 0
      kpList.value = data.kp_list || []
      Object.keys(kpCounts).forEach(k => delete kpCounts[k])
      Object.assign(kpCounts, data.kp_counts || {})
    }
  }catch{ items.value = []; total.value = 0 }
}

watch(() => state.province, () => {
  state.major = ''
  filters.kp = ''
  state.page = 1
  loadMeta()
  loadList()
})
watch(() => state.major, () => { filters.kp = ''; state.page = 1; loadList() })
watch(() => state.pageSize, () => { state.page = 1; loadList() })
watch(() => showImport.value, (v) => { if (v) syncImportForm() })

onMounted(async () => { await loadMeta(); await loadList(); syncImportForm() })

function downloadBlob(blob, filename){
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

async function exportExcel(){
  opMsg.value = ''
  try{
    const { data } = await apiManageSyllabusExport({ province: state.province, major: state.major, fmt: 'excel', kp: filters.kp || undefined })
    downloadBlob(data, `syllabus_${state.province}_${state.major}.xlsx`)
    opOk.value = true; opMsg.value = '已导出 Excel'
  }catch{ opOk.value = false; opMsg.value = '导出失败' }
}
async function exportMarkdown(){
  opMsg.value = ''
  try{
    const { data } = await apiManageSyllabusExport({ province: state.province, major: state.major, fmt: 'md', kp: filters.kp || undefined })
    downloadBlob(data, `syllabus_${state.province}_${state.major}.md`)
    opOk.value = true; opMsg.value = '已导出 Markdown'
  }catch{ opOk.value = false; opMsg.value = '导出失败' }
}
async function downloadTemplate(){
  try{ const { data } = await apiManageSyllabusTemplate(); downloadBlob(data, 'syllabus_template.md') }catch{}
}
async function dedupeDry(){
  opMsg.value = ''
  try{ const { data } = await apiManageSyllabusDedupe({ province: state.province, major: state.major, dry: 1 }); opOk.value = true; opMsg.value = `试运行：发现重复 ${data.duplicates||0} 条，不做删除。` }catch{ opOk.value = false; opMsg.value = '去重试运行失败' }
}
async function dedupeRun(){
  opMsg.value = ''
  try{ const { data } = await apiManageSyllabusDedupe({ province: state.province, major: state.major, dry: 0 }); opOk.value = true; opMsg.value = `已删除重复 ${data.deleted||0} 条。`; await loadList() }catch{ opOk.value = false; opMsg.value = '去重执行失败' }
}
async function renameKp(){
  renameMsg.value = ''
  try{
    const { data } = await apiManageSyllabusRenameKp({ province: state.province, major: state.major, from_kp: renameFrom.value, to_kp: renameTo.value })
    if (data?.success){ renameOk.value = true; renameMsg.value = `已更新 ${data.updated||0} 条，合并 ${data.merged||0} 条。`; renameFrom.value=''; renameTo.value=''; await loadList(); await loadMeta() }
    else { renameOk.value = false; renameMsg.value = data?.error_msg || '重命名失败' }
  }catch{ renameOk.value = false; renameMsg.value = '重命名异常' }
}

const excelInput = ref(null)

function triggerExcel(){ excelInput.value && excelInput.value.click() }
async function onExcelChange(e){
  clearImportFeedback()
  const f = e?.target?.files?.[0]
  if (!f) return
  importExcelName.value = f.name || ''
  const lower = (f.name || '').toLowerCase()
  if (!canUseImportTarget.value){ importOk.value = false; importMsg.value = '请先填写导入目标的省份和专业'; if (excelInput.value) excelInput.value.value = ''; return }
  if (!/\.(xlsx|xls)$/.test(lower)){ importOk.value = false; importMsg.value = '仅支持 .xlsx 或 .xls 文件'; if (excelInput.value) excelInput.value.value = ''; return }
  if (f.size > 10 * 1024 * 1024){ importOk.value = false; importMsg.value = '文件过大，请控制在 10MB 以内'; if (excelInput.value) excelInput.value.value = ''; return }
  importSubmitting.value = true
  try{
    const fd = new FormData()
    fd.append('file', f)
    fd.append('mode', importMode.value)
    fd.append('province', importForm.province)
    fd.append('major', importForm.major)
    const { data } = await apiManageSyllabusImportExcel(fd)
    if (data?.success){
      importOk.value = true
      importMsg.value = 'Excel 导入完成'
      importDetailLines.value = [
        `新增 ${data.created||0} 条`,
        `跳过重复 ${data.skipped||0} 条`,
        `异常 ${data.errors||0} 条`,
        `涉及范围 ${data.pairs||0} 个省份/专业组合`
      ]
      if (Array.isArray(data.error_rows) && data.error_rows.length){
        importDetailLines.value.push(`错误行：${data.error_rows.slice(0, 10).join('、')}${data.error_rows.length > 10 ? ' 等' : ''}`)
      }
      state.province = importForm.province
      state.major = importForm.major
      await loadMeta(); await loadList()
    } else {
      importOk.value = false
      importMsg.value = data?.error_msg || 'Excel 导入失败'
    }
  } catch {
    importOk.value = false
    importMsg.value = 'Excel 导入异常'
  } finally {
    importSubmitting.value = false
    if (excelInput.value) excelInput.value.value = ''
  }
}

async function downloadExcelTemplate(){
  try{ const { data } = await apiManageSyllabusTemplateExcel(); downloadBlob(data, 'syllabus_import_template.xlsx') }catch{}
}
</script>

<style scoped>
/* use global .text-primary/.bg-primary from tokens.css */
</style>
