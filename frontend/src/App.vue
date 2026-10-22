<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

type StoredDocument = {
  id: string
  filename: string
  chunks: number
  uploaded_at: string
}
type Source = {
  marker: string
  filename: string
  locator: string
  excerpt: string
}
type Answer = { answer: string; sources: Source[] }

const documents = ref<StoredDocument[]>([])
const selectedFile = ref<File | null>(null)
const question = ref('What safety controls are documented, and which follow-up actions appear incomplete?')
const result = ref<Answer | null>(null)
const mode = ref<'question' | 'review'>('question')
const loading = ref<'upload' | 'question' | 'review' | 'export' | null>(null)
const notice = ref('')
const error = ref('')
const uploadedCount = computed(() => documents.value.length)

async function parseResponse(response: Response) {
  const json = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(json.detail || `Request failed (${response.status})`)
  return json
}

async function refreshDocuments() {
  try {
    const response = await fetch('/api/documents')
    const json = await parseResponse(response)
    documents.value = json.documents
  } catch {
    // API may not be running when Vue starts; an actionable error appears on request.
  }
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  notice.value = ''
  error.value = ''
}

async function upload() {
  if (!selectedFile.value || loading.value) return
  loading.value = 'upload'
  error.value = ''
  notice.value = ''
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    const data = await parseResponse(await fetch('/api/upload', { method: 'POST', body: form }))
    notice.value = `${data.document.filename} indexed: ${data.document.chunks} searchable chunks.`
    selectedFile.value = null
    const input = document.querySelector<HTMLInputElement>('#file-input')
    if (input) input.value = ''
    await refreshDocuments()
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = null
  }
}

async function ask(review = false) {
  if (loading.value) return
  loading.value = review ? 'review' : 'question'
  error.value = ''
  notice.value = ''
  result.value = null
  mode.value = review ? 'review' : 'question'
  try {
    const path = review ? '/api/analyze' : '/api/chat'
    const payload = review ? { focus: question.value } : { question: question.value }
    result.value = await parseResponse(await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }))
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = null
  }
}

async function exportFile(format: 'pdf' | 'docx' | 'xlsx') {
  if (!result.value || loading.value) return
  loading.value = 'export'
  error.value = ''
  try {
    const response = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: mode.value === 'review' ? 'Preliminary EHS Gap Review' : 'EHS Document Q&A',
        answer: result.value.answer,
        sources: result.value.sources,
        format,
      }),
    })
    if (!response.ok) {
      await parseResponse(response)
    }
    const objectUrl = URL.createObjectURL(await response.blob())
    const anchor = document.createElement('a')
    anchor.href = objectUrl
    anchor.download = `ehs-analysis.${format}`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = null
  }
}

onMounted(refreshDocuments)
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <div class="header-inner">
        <div class="brand">
          <div class="brand-mark">✳</div>
          <div><strong>EHS Insight</strong><span>Document intelligence workspace</span></div>
        </div>
        <span class="header-badge"><span class="status-dot"></span> Portfolio Demo · v0.1</span>
      </div>
    </header>

    <main class="main-content">
      <div class="eyebrow">AI-POWERED EHS INTELLIGENCE</div>
      <div class="hero-row">
        <div>
          <h1>Turn safety documents<br /><em>into actionable insight.</em></h1>
          <p class="hero-description">Search your policies, review incident notes, and prepare evidence-backed draft reports — with source references you can verify.</p>
        </div>
        <div class="hero-stats"><strong>{{ uploadedCount }}</strong><span>Documents indexed</span><small>Local demonstration environment</small></div>
      </div>

      <div class="workspace">
        <aside class="side-panel">
          <section class="panel upload-panel">
            <div class="section-heading"><span class="section-icon">↥</span><h2>Knowledge base</h2></div>
            <p class="muted small">Add EHS policies, inspection records, or incident summaries to analyze.</p>
            <label for="file-input" class="dropzone">
              <span class="upload-symbol">⇧</span>
              <strong>{{ selectedFile?.name ?? 'Choose a document' }}</strong>
              <span>PDF, DOCX, XLSX, or TXT</span>
              <span class="drop-hint">Up to 10 MB per file</span>
            </label>
            <input id="file-input" type="file" accept=".pdf,.docx,.xlsx,.txt" class="visually-hidden" @change="onFileChange" />
            <button class="primary-button full-width" :disabled="!selectedFile || loading !== null" @click="upload">
              {{ loading === 'upload' ? 'Indexing document…' : 'Upload & index document' }}
              <span aria-hidden="true">↗</span>
            </button>
            <p class="privacy-note">Use synthetic or public documents only. Files are sent to an external AI API for processing.</p>
          </section>

          <section class="panel documents-panel">
            <div class="section-heading"><span class="section-icon">▤</span><h2>Indexed files</h2><span class="pill">{{ uploadedCount }}</span></div>
            <div v-if="documents.length === 0" class="empty-list">No documents yet. Try the two synthetic sample files in the project repository.</div>
            <div v-else class="document-list">
              <div v-for="doc in documents" :key="doc.id" class="document-row">
                <span class="file-icon">▤</span>
                <div><strong :title="doc.filename">{{ doc.filename }}</strong><small>{{ doc.chunks }} searchable chunks</small></div>
                <span class="checkmark">✓</span>
              </div>
            </div>
          </section>
        </aside>

        <section class="main-panel panel">
          <div class="assistant-header">
            <div class="section-heading"><span class="section-icon accent">✦</span><div><h2>Intelligence assistant</h2><span class="muted small">Grounded answers from your uploaded evidence</span></div></div>
            <span class="ready-label"><span class="status-dot"></span> Ready to analyze</span>
          </div>

          <div class="prompt-section">
            <label for="question">What would you like to investigate?</label>
            <textarea id="question" v-model="question" rows="4" placeholder="Ask a question about the uploaded documents…"></textarea>
            <div class="example-row"><span>Try:</span>
              <button class="example-chip" @click="question = 'What PPE is required when handling cleaning chemicals?'">PPE requirements</button>
              <button class="example-chip" @click="question = 'Compare the incident note with the written policy. What information is missing?'">Incident gaps</button>
            </div>
            <div class="action-row">
              <button class="primary-button" :disabled="loading !== null || question.trim().length < 3" @click="ask(false)">
                <span>✦</span> {{ loading === 'question' ? 'Searching…' : 'Ask a question' }}
              </button>
              <button class="secondary-button" :disabled="loading !== null || question.trim().length < 3" @click="ask(true)">
                {{ loading === 'review' ? 'Reviewing…' : 'Run preliminary gap review' }} <span>↗</span>
              </button>
            </div>
          </div>

          <div v-if="error" class="alert error" role="alert">{{ error }}. Confirm that the backend is running and your OpenAI API key is configured.</div>
          <div v-if="notice" class="alert success" role="status">{{ notice }}</div>

          <div v-if="result" class="result-card">
            <div class="result-heading"><div><span class="result-label">{{ mode === 'review' ? 'PRELIMINARY REVIEW' : 'GROUNDED RESPONSE' }}</span><h3>{{ mode === 'review' ? 'Findings & follow-up' : 'AI response' }}</h3></div><span class="result-dot">✓</span></div>
            <div class="answer-text">{{ result.answer }}</div>
            <div class="sources-section">
              <h4>Retrieved supporting excerpts <span>{{ result.sources.length }}</span></h4>
              <details v-for="(source, index) in result.sources" :key="index" class="source-item">
                <summary><span class="citation">{{ source.marker }}</span><strong>{{ source.filename }}</strong><span class="source-location">{{ source.locator }}</span></summary>
                <p>{{ source.excerpt }}</p>
              </details>
            </div>
            <div class="export-bar"><div><strong>Export your analysis</strong><span>Prepare a draft for review</span></div>
              <div class="export-buttons">
                <button :disabled="loading !== null" @click="exportFile('pdf')">↓ PDF</button>
                <button :disabled="loading !== null" @click="exportFile('docx')">↓ Word</button>
                <button :disabled="loading !== null" @click="exportFile('xlsx')">↓ Excel</button>
              </div>
            </div>
          </div>
          <div v-else-if="loading === 'question' || loading === 'review'" class="empty-results"><span class="spinner"></span><p>Retrieving evidence and preparing your answer…</p></div>
          <div v-else class="empty-results"><div class="empty-icon">✧</div><strong>Evidence-led analysis starts here</strong><p>Upload the example policy and incident report, then ask a question to see document-aware answers with numbered references.</p></div>
        </section>
      </div>
      <footer><span>EHS Insight · Portfolio demonstration</span><span>AI-generated drafts are not professional safety or legal advice.</span></footer>
    </main>
  </div>
</template>
