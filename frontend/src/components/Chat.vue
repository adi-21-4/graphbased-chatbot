<template>
  <div class="flex h-screen bg-gray-100 font-sans">
    <!-- Sidebar -->
    <div class="w-72 bg-gradient-to-b from-indigo-700 to-blue-900 text-white flex flex-col">
      <div class="p-5 font-bold text-xl border-b border-indigo-500 flex items-center justify-between">
        MKCL Chatbot
      </div>

      <!-- Chat history -->
      <div class="flex-1 overflow-y-auto custom-scroll">
        <div
          v-for="(chat, index) in chats"
          :key="chat.id"
          class="flex items-center justify-between px-4 py-3 cursor-pointer rounded-md mx-2 my-1 transition-all"
          :class="activeChatIndex === index ? 'bg-indigo-500 shadow-lg' : 'hover:bg-indigo-600'"
        >
          <div @click="switchChat(index)" class="flex-1 truncate">
            💬 Chat {{ index + 1 }}
          </div>
          <button
            @click.stop="deleteChat(index)"
            class="ml-2 text-red-300 hover:text-red-500 transition"
            title="Delete chat"
          >
            🗑
          </button>
        </div>
      </div>

      <!-- New chat -->
      <div class="p-4 border-t border-indigo-500">
        <button
          @click="newChat"
          class="w-full py-2 rounded-lg font-semibold shadow-md transition-all bg-gradient-to-r from-green-400 to-green-600 hover:from-green-500 hover:to-green-700 text-white"
        >
          ➕ New Chat
        </button>
      </div>
    </div>

    <!-- Main Chat Window -->
    <div class="flex-1 flex flex-col">
      <!-- Header -->
      <div class="px-6 py-4 bg-gradient-to-r from-indigo-600 to-blue-700 text-white flex justify-between items-center shadow-md sticky top-0">
        <h1 class="font-bold text-lg">Session {{ activeChatIndex + 1 }}</h1>
        <div class="flex items-center gap-3">
          <select v-model="speechLang" class="text-black rounded px-2 py-1">
            <option value="en-IN">English</option>
            <option value="mr-IN">Marathi</option>
          </select>
          <button
            @click="endChat"
            class="px-4 py-2 rounded-lg font-semibold shadow-md transition-all bg-gradient-to-r from-red-500 to-red-700 hover:from-red-600 hover:to-red-800 text-white"
          >
            ❌ End Chat
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div ref="chatWindow" class="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50 custom-scroll">
        <div
          v-for="(msg, idx) in chats[activeChatIndex]?.messages || []"
          :key="idx"
          :class="msg.sender === 'user' ? 'flex justify-end' : 'flex justify-start'"
        >
          <div class="max-w-xs md:max-w-md lg:max-w-lg">
            <div
              :class="[
                'px-4 py-2 rounded-2xl shadow-md text-sm md:text-base',
                msg.sender === 'user'
                  ? 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-br-none'
                  : 'bg-gray-200 text-gray-900 rounded-bl-none'
              ]"
            >
              <!-- ✅ Defensive rendering -->
              <template v-if="msg.type === 'list' ">
                <ul class="list-disc pl-5 space-y-1">
                  <li v-for="(item, i) in Array.isArray(msg.text) ? msg.text : JSON.parse(msg.text)" :key="i">
                    {{ item }}
                  </li>
                </ul>
              </template>
              <template v-else>
                <p>{{ msg.text }}</p>
              </template>
            </div>
            <div
              class="text-xs text-gray-400 mt-1"
              :class="msg.sender === 'user' ? 'text-right' : 'text-left'"
            >
              {{ msg.time }}
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <form @submit.prevent="sendQuestion" class="flex items-center gap-2 p-4 border-t bg-gray-100 sticky bottom-0">
        <input
          v-model="question"
          type="text"
          placeholder="Type or speak your question..."
          class="flex-1 border border-gray-300 rounded-xl px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
        />
        <button
          type="button"
          @click="toggleListening"
          class="p-3 rounded-full bg-gradient-to-r from-green-400 to-green-600 hover:from-green-500 hover:to-green-700 text-white shadow-md"
          :title="listening ? 'Stop Listening' : 'Start Listening'"
        >
          🎤
        </button>
        <button
          type="submit"
          class="px-6 py-2 rounded-xl font-semibold shadow-md transition-all bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white"
        >
          Send ➤
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import axios from 'axios'

const question = ref('')
const speechLang = ref('en-IN')
const listening = ref(false)
const isSpeechInput = ref(false)

const chats = ref([{ id: Date.now(), messages: [] }])
const activeChatIndex = ref(0)

let recognition = null
const chatWindow = ref(null)

watch(
  () => chats.value[activeChatIndex.value]?.messages,
  async () => {
    await nextTick()
    if (chatWindow.value) {
      chatWindow.value.scrollTop = chatWindow.value.scrollHeight
    }
  }
)

// Speech recognition
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition = new SpeechRecognition()
  recognition.interimResults = false
  recognition.maxAlternatives = 1

  recognition.onresult = (event) => {
    question.value = event.results[0][0].transcript
    listening.value = false
    isSpeechInput.value = true
    sendQuestion()
  }
  recognition.onerror = () => (listening.value = false)
  recognition.onend = () => (listening.value = false)
}

function toggleListening() {
  if (!recognition) return alert('Speech recognition not supported')
  
  if (listening.value) {
    recognition.stop()
  } else {
    recognition.lang = speechLang.value 
    recognition.start()
  }
  
  listening.value = !listening.value
}
async function sendQuestion() {
  if (!question.value.trim()) return
  const userMessage = question.value
  chats.value[activeChatIndex.value].messages.push({
    sender: 'user',
    text: userMessage,
    type: 'text',
    time: new Date().toLocaleTimeString()
  })
  question.value = ''

  try {
    const res = await axios.post('http://127.0.0.1:5000/ask', {
      question: userMessage,
      speech_mode: isSpeechInput.value,
      speech_lang: speechLang.value
    })
    const answer = res.data.answer
    chats.value[activeChatIndex.value].messages.push({
      sender: 'bot',
      text: answer,
      type: res.data.type || 'text',
      time: new Date().toLocaleTimeString()
    })
    saveChats()
  } catch (err) {
    chats.value[activeChatIndex.value].messages.push({
      sender: 'bot',
      text: err.response?.data?.error || 'Something went wrong',
      type: 'text',
      time: new Date().toLocaleTimeString()
    })
  } finally {
    isSpeechInput.value = false
  }
}

function newChat() {
  chats.value.push({ id: Date.now(), messages: [] })
  activeChatIndex.value = chats.value.length - 1
  saveChats()
}
function switchChat(index) {
  activeChatIndex.value = index
}
function endChat() {
  chats.value[activeChatIndex.value].messages.push({
    sender: 'bot',
    text: '🔒 This chat has been ended.',
    type: 'text',
    time: new Date().toLocaleTimeString()
  })
  saveChats()
}
function deleteChat(index) {
  chats.value.splice(index, 1)
  if (activeChatIndex.value >= chats.value.length) activeChatIndex.value = chats.value.length - 1
  if (chats.value.length === 0) newChat()
  saveChats()
}

// LocalStorage persistence
function saveChats() {
  localStorage.setItem('mkcl_chats', JSON.stringify(chats.value))
}
function loadChats() {
  const saved = localStorage.getItem('mkcl_chats')
  if (saved) chats.value = JSON.parse(saved)
}
loadChats()
</script>

<style>
/* Custom scrollbar */
.custom-scroll::-webkit-scrollbar {
  width: 8px;
}
.custom-scroll::-webkit-scrollbar-thumb {
  background: #a5b4fc; /* indigo-300 */
  border-radius: 4px;
}
.custom-scroll::-webkit-scrollbar-thumb:hover {
  background: #6366f1; /* indigo-500 */
}
</style>
